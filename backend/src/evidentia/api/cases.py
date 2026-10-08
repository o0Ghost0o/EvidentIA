"""Case workspaces: CRUD, evidence links, review trail, trees and briefs."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from evidentia import models
from evidentia.db import SessionDep

router = APIRouter(prefix="/cases", tags=["cases"])

REVIEW_STATES = (
    "nuevo", "en_revision", "requiere_evidencia", "aprobado_borrador", "descartado",
)
SOURCE_KINDS = ("news", "indicator", "event")


class CaseCreate(BaseModel):
    titulo: str = Field(min_length=1, max_length=300)
    modalidad: str = Field(default="tvn", pattern="^(tvn|banca)$")
    queries: list[str] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


def _infer_source_type(ev_id: str) -> str:
    if ev_id.startswith("evt-"):
        return "event"
    if ev_id.startswith("ind-") or (":" in ev_id and not ev_id.startswith("http")):
        return "indicator"
    if ev_id.startswith("doc-") or ev_id.startswith("res-"):
        return "document"
    return "news"


class CaseUpdate(BaseModel):
    titulo: str | None = Field(default=None, min_length=1, max_length=300)
    estado: str | None = None
    flags: list[str] | None = None


class FlagRequest(BaseModel):
    flag: str = Field(min_length=1, max_length=64)


class EvidenceCreate(BaseModel):
    fuente_tipo: str = Field(pattern="^(news|indicator|event|document)$")
    fuente_id: str = Field(min_length=1, max_length=128)
    rol: str = Field(default="respaldo", max_length=32)
    nota: str | None = None
    marcado_manual: bool = True


class NoteCreate(BaseModel):
    autor: str = Field(min_length=1, max_length=128)
    estado_revision: str
    texto: str = Field(min_length=1)


def _get_case(session: Session, case_id: int) -> models.Case:
    case = session.get(models.Case, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="case not found")
    return case


def _compute_activity_flags(
    case: models.Case,
    evidence: list[models.EvidenceItem],
    notes: list[models.VerificationNote],
) -> list[dict[str, str]]:
    """Generate activity and state badges reflecting client actions and lead status."""
    flags: list[dict[str, str]] = []

    # 1. Custom client flags
    for flag_name in (case.flags or []):
        flags.append({
            "id": f"custom-{flag_name}",
            "label": flag_name,
            "category": "custom",
            "variant": "outline",
            "description": "Flag personalizada asignada al lead",
        })

    # 2. Status / lifecycle badges
    estado_labels = {
        "nuevo": ("Nuevo Lead", "secondary", "Lead registrado en el sistema"),
        "en_revision": ("En Revisión", "warning", "Revisión activa por el equipo"),
        "requiere_evidencia": ("Requiere Evidencia", "destructive", "Requiere más fuentes o sustento"),
        "aprobado_borrador": ("Borrador Aprobado", "success", "Aprobado para informe"),
        "descartado": ("Descartado", "destructive", "Lead descartado"),
    }
    if case.estado in estado_labels:
        lbl, var, desc = estado_labels[case.estado]
        flags.append({
            "id": f"status-{case.estado}",
            "label": lbl,
            "category": "status",
            "variant": var,
            "description": desc,
        })

    # 3. Evidence actions performed by client
    ev_count = len(evidence)
    if ev_count > 0:
        flags.append({
            "id": "action-evidence-linked",
            "label": f"{ev_count} Evidencia(s)",
            "category": "action",
            "variant": "info",
            "description": f"El cliente/usuario vinculó {ev_count} ficha(s) de evidencia",
        })

    manual_count = sum(1 for e in evidence if e.marcado_manual)
    if manual_count > 0:
        flags.append({
            "id": "action-manual-marking",
            "label": f"Marcado Manual ({manual_count})",
            "category": "action",
            "variant": "purple",
            "description": f"Se marcaron manualmente {manual_count} evidencia(s)",
        })

    # 4. Source types linked
    source_kinds = {e.fuente_tipo for e in evidence}
    if "news" in source_kinds:
        flags.append({
            "id": "source-news",
            "label": "Noticias / Prensa",
            "category": "source",
            "variant": "secondary",
            "description": "Contiene noticias y artículos de prensa",
        })
    if "indicator" in source_kinds:
        flags.append({
            "id": "source-indicator",
            "label": "Datos Macroeconómicos",
            "category": "source",
            "variant": "teal",
            "description": "Contiene indicadores del Banco Mundial",
        })
    if "event" in source_kinds:
        flags.append({
            "id": "source-event",
            "label": "Alerta Geosísmica",
            "category": "source",
            "variant": "warning",
            "description": "Contiene eventos geosísmicos USGS",
        })
    if "document" in source_kinds:
        flags.append({
            "id": "source-document",
            "label": "Documentos oficiales",
            "category": "source",
            "variant": "info",
            "description": "Contiene documentos y fuentes primarias",
        })

    # 5. Review trail actions
    if notes:
        flags.append({
            "id": "action-notes",
            "label": f"{len(notes)} Nota(s) Auditoría",
            "category": "action",
            "variant": "teal",
            "description": f"El cliente/analista registró {len(notes)} nota(s) de revisión",
        })

    # 6. Modality
    flags.append({
        "id": f"modality-{case.modalidad}",
        "label": f"Modalidad: {case.modalidad.upper()}",
        "category": "modality",
        "variant": "outline",
        "description": f"Lead configurado en modalidad {case.modalidad}",
    })

    return flags


def _auto_link_cluster_evidence(session: Session, case: models.Case) -> list[models.EvidenceItem]:
    """Auto-link event cluster evidence if the case has 0 evidence items."""
    existing = session.exec(
        select(models.EvidenceItem).where(models.EvidenceItem.case_id == case.id)
    ).all()
    if existing:
        return list(existing)

    group_ids = [f for f in (case.flags or []) if f.startswith("evt-")]
    candidate_articles: list[models.NewsArticle] = []

    if group_ids:
        candidate_articles = list(session.exec(
            select(models.NewsArticle).where(models.NewsArticle.grupo_evento_id.in_(group_ids))
        ).all())

    if not candidate_articles:
        candidate_articles = list(session.exec(
            select(models.NewsArticle).where(models.NewsArticle.titulo == case.titulo)
        ).all())

    if not candidate_articles and case.queries:
        for q in case.queries:
            if q and q.strip():
                candidate_articles = list(session.exec(
                    select(models.NewsArticle).where(models.NewsArticle.titulo == q.strip())
                ).all())
                if candidate_articles:
                    break

    target_articles: list[models.NewsArticle] = []
    if candidate_articles:
        detected_groups = {a.grupo_evento_id for a in candidate_articles if a.grupo_evento_id}
        if detected_groups:
            target_articles = list(session.exec(
                select(models.NewsArticle).where(
                    models.NewsArticle.grupo_evento_id.in_(list(detected_groups))
                )
            ).all())
        else:
            target_articles = candidate_articles

    created_items: list[models.EvidenceItem] = []
    for art in target_articles:
        item = models.EvidenceItem(
            case_id=case.id,
            fuente_tipo="news",
            fuente_id=art.id_noticia,
            rol="respaldo",
            marcado_manual=False,
        )
        session.add(item)
        created_items.append(item)

    if created_items:
        session.commit()
        return created_items

    return []


def _case_detail(session: Session, case: models.Case) -> dict:
    evidence = session.exec(
        select(models.EvidenceItem).where(models.EvidenceItem.case_id == case.id)
    ).all()
    if not evidence:
        evidence = _auto_link_cluster_evidence(session, case)
    notes = session.exec(
        select(models.VerificationNote).where(models.VerificationNote.case_id == case.id)
    ).all()
    activity_flags = _compute_activity_flags(case, evidence, notes)
    return {
        "id": case.id, "titulo": case.titulo, "modalidad": case.modalidad,
        "queries": case.queries, "estado": case.estado,
        "flags": case.flags or [],
        "activity_flags": activity_flags,
        "created_at": case.created_at, "updated_at": case.updated_at,
        "evidence": [
            {"id": e.id, "fuente_tipo": e.fuente_tipo, "fuente_id": e.fuente_id,
             "rol": e.rol, "nota": e.nota, "marcado_manual": e.marcado_manual}
            for e in evidence
        ],
        "notes": [
            {"id": n.id, "autor": n.autor, "estado_revision": n.estado_revision,
             "texto": n.texto, "created_at": n.created_at}
            for n in notes
        ],
    }


@router.post("", status_code=201)
def create_case(payload: CaseCreate, session: SessionDep) -> dict:
    case = models.Case(
        titulo=payload.titulo,
        modalidad=payload.modalidad,
        queries=payload.queries,
        flags=payload.flags,
    )
    session.add(case)
    session.commit()
    session.refresh(case)

    # Automatically link evidence sources if supplied
    for ev_id in payload.evidence_ids:
        tipo = _infer_source_type(ev_id)
        item = models.EvidenceItem(
            case_id=case.id,
            fuente_tipo=tipo,
            fuente_id=ev_id,
            rol="respaldo",
            marcado_manual=False,
        )
        session.add(item)
    if payload.evidence_ids:
        session.commit()
        session.refresh(case)
    else:
        _auto_link_cluster_evidence(session, case)

    return _case_detail(session, case)


@router.get("")
def list_cases(session: SessionDep, modalidad: str | None = None) -> dict:
    query = select(models.Case)
    if modalidad:
        query = query.where(models.Case.modalidad == modalidad)
    cases = session.exec(query).all()
    return {"count": len(cases), "items": [_case_detail(session, c) for c in cases]}


@router.get("/{case_id}")
def get_case(case_id: int, session: SessionDep) -> dict:
    return _case_detail(session, _get_case(session, case_id))


@router.patch("/{case_id}")
def update_case(case_id: int, payload: CaseUpdate, session: SessionDep) -> dict:
    case = _get_case(session, case_id)
    if payload.titulo is not None:
        case.titulo = payload.titulo
    if payload.estado is not None:
        if payload.estado not in REVIEW_STATES:
            raise HTTPException(status_code=422, detail=f"estado must be one of {REVIEW_STATES}")
        case.estado = payload.estado
    if payload.flags is not None:
        case.flags = payload.flags
    case.updated_at = datetime.now(timezone.utc)
    session.add(case)
    session.commit()
    session.refresh(case)
    return _case_detail(session, case)


@router.post("/{case_id}/flags", status_code=200)
def add_flag(case_id: int, payload: FlagRequest, session: SessionDep) -> dict:
    case = _get_case(session, case_id)
    flag = payload.flag.strip()
    current_flags = list(case.flags or [])
    if flag and flag not in current_flags:
        current_flags.append(flag)
        case.flags = current_flags
        case.updated_at = datetime.now(timezone.utc)
        session.add(case)
        session.commit()
        session.refresh(case)
    return _case_detail(session, case)


@router.delete("/{case_id}/flags/{flag_name}", status_code=200)
def remove_flag(case_id: int, flag_name: str, session: SessionDep) -> dict:
    case = _get_case(session, case_id)
    current_flags = list(case.flags or [])
    if flag_name in current_flags:
        current_flags.remove(flag_name)
        case.flags = current_flags
        case.updated_at = datetime.now(timezone.utc)
        session.add(case)
        session.commit()
        session.refresh(case)
    return _case_detail(session, case)


@router.delete("/{case_id}", status_code=204)
def delete_case(case_id: int, session: SessionDep) -> Response:
    case = _get_case(session, case_id)
    for item in session.exec(
        select(models.EvidenceItem).where(models.EvidenceItem.case_id == case.id)
    ).all():
        session.delete(item)
    for note in session.exec(
        select(models.VerificationNote).where(models.VerificationNote.case_id == case.id)
    ).all():
        session.delete(note)
    session.delete(case)
    session.commit()
    return Response(status_code=204)


@router.post("/{case_id}/evidence", status_code=201)
def add_evidence(case_id: int, payload: EvidenceCreate, session: SessionDep) -> dict:
    _get_case(session, case_id)
    item = models.EvidenceItem(
        case_id=case_id, fuente_tipo=payload.fuente_tipo, fuente_id=payload.fuente_id,
        rol=payload.rol, nota=payload.nota, marcado_manual=payload.marcado_manual,
    )
    session.add(item)
    session.commit()
    session.refresh(item)
    return {"id": item.id, "fuente_tipo": item.fuente_tipo, "fuente_id": item.fuente_id}


@router.delete("/{case_id}/evidence/{evidence_id}", status_code=204)
def remove_evidence(case_id: int, evidence_id: int, session: SessionDep) -> Response:
    item = session.get(models.EvidenceItem, evidence_id)
    if item is None or item.case_id != case_id:
        raise HTTPException(status_code=404, detail="evidence not found")
    session.delete(item)
    session.commit()
    return Response(status_code=204)


@router.post("/{case_id}/notes", status_code=201)
def add_note(case_id: int, payload: NoteCreate, session: SessionDep) -> dict:
    case = _get_case(session, case_id)
    if payload.estado_revision not in REVIEW_STATES:
        raise HTTPException(status_code=422, detail=f"estado_revision must be one of {REVIEW_STATES}")
    note = models.VerificationNote(
        case_id=case.id, autor=payload.autor,
        estado_revision=payload.estado_revision, texto=payload.texto,
    )
    session.add(note)
    case.estado = payload.estado_revision
    case.updated_at = datetime.now(timezone.utc)
    session.add(case)
    session.commit()
    session.refresh(note)
    return {"id": note.id, "estado_revision": note.estado_revision}


@router.get("/{case_id}/tree")
def case_tree(case_id: int, session: SessionDep, depth: int = Query(default=5, ge=1, le=10)) -> dict:
    """Merged evidence trees up to specified depth (default 5 levels) plus the case node."""
    from evidentia.graph.graph_service import evidence_tree

    case = _get_case(session, case_id)
    items = session.exec(
        select(models.EvidenceItem).where(models.EvidenceItem.case_id == case.id)
    ).all()
    if not items:
        items = _auto_link_cluster_evidence(session, case)

    nodes: dict[tuple[str, str], dict] = {("case", str(case.id)): {
        "tipo": "case", "id": str(case.id), "label": case.titulo,
    }}
    edges_map: dict[tuple[str, str, str, str, str], dict] = {}

    for item in items:
        edge_key = ("case", str(case.id), item.fuente_tipo, item.fuente_id, "has_evidence")
        edges_map[edge_key] = {
            "origen_tipo": "case", "origen_id": str(case.id),
            "destino_tipo": item.fuente_tipo, "destino_id": item.fuente_id,
            "tipo": "has_evidence", "peso": 1.0,
        }
        sub = evidence_tree(session, item.fuente_tipo, item.fuente_id, depth=depth)
        for node in sub["nodes"]:
            nodes.setdefault((node["tipo"], node["id"]), node)
        for e in sub["edges"]:
            ek = (e["origen_tipo"], e["origen_id"], e["destino_tipo"], e["destino_id"], e.get("tipo", ""))
            edges_map[ek] = e

    # Ensure all direct relations between the linked items are included
    if len(items) > 1:
        item_ids = [it.fuente_id for it in items]
        inter_rels = session.exec(
            select(models.Relation).where(
                models.Relation.origen_id.in_(item_ids),
                models.Relation.destino_id.in_(item_ids),
            )
        ).all()
        for r in inter_rels:
            rk = (r.origen_tipo, r.origen_id, r.destino_tipo, r.destino_id, r.tipo)
            edges_map[rk] = {
                "origen_tipo": r.origen_tipo, "origen_id": r.origen_id,
                "destino_tipo": r.destino_tipo, "destino_id": r.destino_id,
                "tipo": r.tipo, "peso": r.peso,
            }

    return {"root": {"tipo": "case", "id": str(case.id)}, "nodes": list(nodes.values()), "edges": list(edges_map.values())}


def _evidence_docs(session: Session, case: models.Case) -> tuple[list, list[str]]:
    """Resolve evidence items to synthesiser docs; returns (docs, missing)."""
    from evidentia.generation.synthesizer import EvidenceDoc
    from evidentia.retrieval.chunking import build_indicator_parent

    docs: list[EvidenceDoc] = []
    missing: list[str] = []
    items = session.exec(
        select(models.EvidenceItem).where(models.EvidenceItem.case_id == case.id)
    ).all()
    for item in items:
        if item.fuente_tipo == "news":
            obj = session.exec(
                select(models.NewsArticle).where(models.NewsArticle.id_noticia == item.fuente_id)
            ).first()
            if obj is None:
                missing.append(f"news:{item.fuente_id}")
                continue
            docs.append(EvidenceDoc(
                source_id=obj.id_noticia, kind="news", text=obj.titulo or "",
                trace={"medio": obj.medio, "fecha": str(obj.fecha_publicacion or ""),
                       "url": obj.url, "alcance_texto": obj.alcance_texto,
                       "agencia": obj.agencia_primaria or ""},
            ))
        elif item.fuente_tipo == "indicator":
            try:
                pais, indicador_id, anio = item.fuente_id.split(":")
                obj = session.exec(
                    select(models.Indicator).where(
                        models.Indicator.pais_iso3 == pais,
                        models.Indicator.indicador_id == indicador_id,
                        models.Indicator.anio == int(anio),
                    )
                ).first()
            except ValueError:
                obj = None
            if obj is None:
                missing.append(f"indicator:{item.fuente_id}")
                continue
            parent = build_indicator_parent({
                "pais_iso3": obj.pais_iso3, "indicador_id": obj.indicador_id,
                "anio": obj.anio, "valor": obj.valor, "unidad": obj.unidad or "",
                "fuente_url": obj.fuente_url or "",
            })
            docs.append(EvidenceDoc(
                source_id=item.fuente_id, kind="indicator",
                text=parent.page_content, trace={"fuente": "Banco Mundial"},
            ))
        elif item.fuente_tipo == "event":
            obj = session.exec(
                select(models.GeoEvent).where(models.GeoEvent.event_id == item.fuente_id)
            ).first()
            if obj is None:
                missing.append(f"event:{item.fuente_id}")
                continue
            docs.append(EvidenceDoc(
                source_id=obj.event_id, kind="event",
                text=f"Sismo magnitud {obj.magnitude} en {obj.place} ({obj.time}).",
                trace={"fuente": "USGS", "url": obj.url or ""},
            ))
    return docs, missing


@router.post("/{case_id}/brief", response_model=None)
def generate_brief(
    case_id: int, session: SessionDep,
    formato: str = Query(default="json", pattern="^(json|markdown)$"),
) -> Response | dict:
    """Generate the modality brief/bulletin from linked evidence (or abstain)."""
    from evidentia.briefs import banca, tvn

    case = _get_case(session, case_id)
    docs, missing = _evidence_docs(session, case)
    package = (
        tvn.build_tvn_package(docs) if case.modalidad == "tvn"
        else banca.build_banca_bulletin(docs)
    )
    package["missing_sources"] = missing
    if formato == "markdown":
        text = (
            tvn.render_markdown(package, case.titulo) if case.modalidad == "tvn"
            else banca.render_markdown(package, case.titulo)
        )
        return Response(content=text, media_type="text/markdown")
    return package
