"""Evidence-tree queries and item detail resolution over the provenance graph."""

from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select, or_

from evidentia import models
from evidentia.db import SessionDep
from evidentia.graph.graph_service import evidence_tree
from evidentia.retrieval.chunking import COUNTRY_NAMES, INDICATOR_NAMES

router = APIRouter(prefix="/evidence", tags=["evidence"])


class EvidenceItemDetail(BaseModel):
    tipo: str  # news | indicator | event | entity | case
    id: str
    titulo: str
    descripcion: Optional[str] = None
    url: Optional[str] = None
    fuente_nombre: Optional[str] = None
    fecha: Optional[str] = None
    detalles: dict[str, Any] = Field(default_factory=dict)
    relaciones: list[dict[str, Any]] = Field(default_factory=list)


def _resolve_evidence_item(session: Session, tipo: str, id_val: str) -> EvidenceItemDetail:
    tipo = tipo.lower().strip()
    id_clean = id_val.strip()

    if id_clean.startswith(f"{tipo}:"):
        id_clean = id_clean[len(f"{tipo}:"):]

    if tipo == "news":
        article = session.exec(
            select(models.NewsArticle).where(
                or_(
                    models.NewsArticle.id_noticia == id_clean,
                    models.NewsArticle.url == id_clean,
                )
            )
        ).first()
        if article is None and id_clean.isdigit():
            article = session.get(models.NewsArticle, int(id_clean))

        if article is None:
            raise HTTPException(status_code=404, detail=f"News article '{id_clean}' not found")

        rels = session.exec(
            select(models.Relation).where(
                or_(
                    (models.Relation.origen_tipo == "news") & (models.Relation.origen_id == article.id_noticia),
                    (models.Relation.destino_tipo == "news") & (models.Relation.destino_id == article.id_noticia),
                )
            )
        ).all()

        formatted_rels = [
            {
                "origen_tipo": r.origen_tipo,
                "origen_id": r.origen_id,
                "destino_tipo": r.destino_tipo,
                "destino_id": r.destino_id,
                "tipo": r.tipo,
                "peso": r.peso,
            }
            for r in rels
        ]

        fecha_str = None
        if article.fecha_publicacion:
            fecha_str = article.fecha_publicacion.isoformat()
        elif article.fecha_extraccion:
            fecha_str = article.fecha_extraccion.isoformat()

        return EvidenceItemDetail(
            tipo="news",
            id=article.id_noticia,
            titulo=article.titulo,
            descripcion=f"Titular publicado por {article.medio}. Alcance textual: {article.alcance_texto}.",
            url=article.url,
            fuente_nombre=article.medio or "Medio Informativo",
            fecha=fecha_str,
            detalles={
                "id_noticia": article.id_noticia,
                "medio": article.medio,
                "idioma": article.idioma,
                "alcance_texto": article.alcance_texto,
                "origen": article.origen,
                "agencia_primaria": article.agencia_primaria,
                "grupo_evento_id": article.grupo_evento_id,
                "tema": article.tema,
            },
            relaciones=formatted_rels,
        )

    elif tipo == "indicator":
        indicator: models.Indicator | None = None
        if ":" in id_clean:
            parts = id_clean.split(":")
            if len(parts) == 3:
                pais, ind_id, anio = parts
                try:
                    indicator = session.exec(
                        select(models.Indicator).where(
                            models.Indicator.pais_iso3 == pais.upper(),
                            models.Indicator.indicador_id == ind_id,
                            models.Indicator.anio == int(anio),
                        )
                    ).first()
                except ValueError:
                    pass
        if indicator is None:
            indicator = session.exec(
                select(models.Indicator)
                .where(models.Indicator.indicador_id == id_clean)
                .order_by(models.Indicator.anio.desc())
            ).first()

        if indicator is None and id_clean.isdigit():
            indicator = session.get(models.Indicator, int(id_clean))

        if indicator is None:
            raise HTTPException(status_code=404, detail=f"Indicator '{id_clean}' not found")

        pais_nombre = COUNTRY_NAMES.get(indicator.pais_iso3, indicator.pais_iso3)
        indicador_nombre = INDICATOR_NAMES.get(indicator.indicador_id, indicator.indicador_id)
        valor_str = f"{indicator.valor} {indicator.unidad or ''}".strip() if indicator.valor is not None else "Sin dato publicado"

        return EvidenceItemDetail(
            tipo="indicator",
            id=f"{indicator.pais_iso3}:{indicator.indicador_id}:{indicator.anio}",
            titulo=f"{pais_nombre} · {indicador_nombre} ({indicator.anio})",
            descripcion=f"Valor observado: {valor_str}. Observación oficial provista bajo licencia {indicator.licencia}.",
            url=indicator.fuente_url or "https://data.worldbank.org/",
            fuente_nombre="Banco Mundial (World Bank Open Data)",
            fecha=str(indicator.anio),
            detalles={
                "pais_iso3": indicator.pais_iso3,
                "pais_nombre": pais_nombre,
                "indicador_id": indicator.indicador_id,
                "indicador_nombre": indicador_nombre,
                "anio": indicator.anio,
                "valor": indicator.valor,
                "unidad": indicator.unidad,
                "licencia": indicator.licencia,
            },
            relaciones=[],
        )

    elif tipo == "event":
        event = session.exec(
            select(models.GeoEvent).where(models.GeoEvent.event_id == id_clean)
        ).first()
        if event is None and id_clean.isdigit():
            event = session.get(models.GeoEvent, int(id_clean))

        if event is None:
            raise HTTPException(status_code=404, detail=f"Event '{id_clean}' not found")

        place_str = event.place or "Ubicación no especificada"
        mag_str = f"M{event.magnitude}" if event.magnitude is not None else "Magnitud N/D"
        fecha_str = event.time.isoformat() if event.time else None

        return EvidenceItemDetail(
            tipo="event",
            id=event.event_id,
            titulo=f"Evento Sísmico {mag_str} — {place_str}",
            descripcion=f"Sismo de magnitud {event.magnitude} registrado a {event.depth or 0} km de profundidad. Estado: {event.status or 'revisado'}.",
            url=event.url or f"https://earthquake.usgs.gov/earthquakes/eventpage/{event.event_id}",
            fuente_nombre="USGS Earthquake Hazards Program",
            fecha=fecha_str,
            detalles={
                "event_id": event.event_id,
                "magnitude": event.magnitude,
                "place": event.place,
                "depth": event.depth,
                "latitude": event.latitude,
                "longitude": event.longitude,
                "status": event.status,
            },
            relaciones=[],
        )

    elif tipo == "entity":
        entity: models.Entity | None = None
        if id_clean.isdigit():
            entity = session.get(models.Entity, int(id_clean))
        if entity is None:
            entity = session.exec(
                select(models.Entity).where(
                    or_(
                        models.Entity.normalizado == id_clean.lower(),
                        models.Entity.nombre == id_clean,
                    )
                )
            ).first()

        if entity is None:
            raise HTTPException(status_code=404, detail=f"Entity '{id_clean}' not found")

        rels = session.exec(
            select(models.Relation).where(
                or_(
                    (models.Relation.destino_tipo == "entity") & (models.Relation.destino_id == str(entity.id)),
                    (models.Relation.origen_tipo == "entity") & (models.Relation.origen_id == str(entity.id)),
                )
            )
        ).all()

        formatted_rels = [
            {
                "origen_tipo": r.origen_tipo,
                "origen_id": r.origen_id,
                "destino_tipo": r.destino_tipo,
                "destino_id": r.destino_id,
                "tipo": r.tipo,
                "peso": r.peso,
            }
            for r in rels
        ]

        return EvidenceItemDetail(
            tipo="entity",
            id=str(entity.id),
            titulo=f"{entity.nombre} ({entity.tipo})",
            descripcion=f"Entidad de tipo {entity.tipo} registrada en el grafo de conocimiento ({len(rels)} conexiones).",
            fuente_nombre="Grafo de Entidades EvidentIA",
            detalles={
                "id": entity.id,
                "nombre": entity.nombre,
                "tipo": entity.tipo,
                "normalizado": entity.normalizado,
                "menciones_count": len(rels),
            },
            relaciones=formatted_rels,
        )

    elif tipo == "case":
        case_obj: models.Case | None = None
        if id_clean.isdigit():
            case_obj = session.get(models.Case, int(id_clean))
        if case_obj is None:
            raise HTTPException(status_code=404, detail=f"Case '{id_clean}' not found")

        return EvidenceItemDetail(
            tipo="case",
            id=str(case_obj.id),
            titulo=case_obj.titulo,
            descripcion=f"Lead de modalidad {case_obj.modalidad}. Estado actual: {case_obj.estado}.",
            fuente_nombre="EvidentIA Editorial Desk",
            fecha=case_obj.created_at.isoformat() if case_obj.created_at else None,
            detalles={
                "id": case_obj.id,
                "modalidad": case_obj.modalidad,
                "estado": case_obj.estado,
                "queries": case_obj.queries,
                "flags": case_obj.flags,
            },
            relaciones=[],
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported evidence type: '{tipo}'")


@router.get("/tree")
def get_tree(
    session: SessionDep,
    tipo: str = Query(pattern="^(news|indicator|event|entity)$"),
    id: str = Query(min_length=1),
    depth: int = Query(default=5, ge=1, le=10),
) -> dict:
    """Return the neighbourhood of any graph node as nodes + typed edges."""
    return evidence_tree(session, tipo, id, depth=depth)


@router.get("/item/{tipo}/{item_id:path}", response_model=EvidenceItemDetail)
def get_evidence_item_by_path(
    tipo: str,
    item_id: str,
    session: SessionDep,
) -> EvidenceItemDetail:
    """Resolve enriched details of an evidence item by type and path ID."""
    return _resolve_evidence_item(session, tipo, item_id)


@router.get("/item", response_model=EvidenceItemDetail)
def get_evidence_item_by_query(
    session: SessionDep,
    tipo: str = Query(min_length=1),
    id: str = Query(min_length=1),
) -> EvidenceItemDetail:
    """Resolve enriched details of an evidence item by type and query ID."""
    return _resolve_evidence_item(session, tipo, id)


@router.get("/graph")
def get_global_graph(
    session: SessionDep,
    limit_relations: int = Query(default=250, ge=10, le=1000),
) -> dict:
    """Return the global GraphRAG knowledge graph with nodes and typed relations."""
    from evidentia.graph.graph_service import _node_label

    rels = session.exec(select(models.Relation).limit(limit_relations)).all()
    node_keys: set[tuple[str, str]] = set()
    links: list[dict[str, Any]] = []

    for r in rels:
        src = f"{r.origen_tipo}:{r.origen_id}"
        dst = f"{r.destino_tipo}:{r.destino_id}"
        node_keys.add((r.origen_tipo, r.origen_id))
        node_keys.add((r.destino_tipo, r.destino_id))
        links.append({
            "source": src,
            "target": dst,
            "tipo": r.tipo,
            "peso": r.peso,
        })

    # Also include existing cases and their linked evidence
    cases = session.exec(select(models.Case).limit(20)).all()
    for c in cases:
        if c.id is None:
            continue
        c_key = ("case", str(c.id))
        node_keys.add(c_key)
        ev_items = session.exec(
            select(models.EvidenceItem).where(models.EvidenceItem.case_id == c.id)
        ).all()
        for ev in ev_items:
            ev_key = f"{ev.fuente_tipo}:{ev.fuente_id}"
            node_keys.add((ev.fuente_tipo, ev.fuente_id))
            links.append({
                "source": f"case:{c.id}",
                "target": ev_key,
                "tipo": "has_evidence",
                "peso": 1.0,
            })

    nodes: list[dict[str, Any]] = []
    for tipo, ref in node_keys:
        label = _node_label(tipo, ref, session)
        nodes.append({
            "id": f"{tipo}:{ref}",
            "ref": ref,
            "tipo": tipo,
            "label": label,
        })

    return {
        "nodes": nodes,
        "links": links,
        "total_nodes": len(nodes),
        "total_links": len(links),
    }

