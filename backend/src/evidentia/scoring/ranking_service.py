"""Multi-modal ranking inbox service.

Generates and persists the prioritised inbox across all ingested data families:
- News articles and deduplicated event groups (TVN + GDELT + Wire)
- Macroeconomic indicators (World Bank series for Panama & region)
- Geophysical seismic events (USGS Earthquake Hazards Program)

Deterministic attention scoring ensures total reproducibility and traceability.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlmodel import Session, select

from evidentia import models
from evidentia.config import get_settings, resolve_data_path
from evidentia.scoring import score as scoring
from evidentia.scoring.deduplication import label_group

logger = logging.getLogger(__name__)

# Indicator & Country label dictionaries
INDICATOR_NAMES: dict[str, str] = {
    "NY.GDP.MKTP.KD.ZG": "Crecimiento del PIB (% anual)",
    "FP.CPI.TOTL.ZG": "Inflación al Consumidor (% anual)",
    "SL.UEM.TOTL.ZS": "Tasa de Desempleo (% fuerza laboral)",
    "SP.POP.TOTL": "Población Total",
    "IT.NET.USER.ZS": "Usuarios de Internet (% población)",
    "NE.EXP.GNFS.ZS": "Exportaciones de Bienes y Servicios (% PIB)",
    "EG.ELC.ACCS.ZS": "Acceso a la Electricidad (% población)",
    "SI.POV.NAHC": "Tasa de Pobreza Nacional (% población)",
    "SE.PRM.CMPT.ZS": "Finalización de Educación Primaria (%)",
    "SH.DYN.MORT": "Mortalidad Infantil (por 1.000 nacidos)",
}

COUNTRY_NAMES: dict[str, str] = {
    "PAN": "Panamá",
    "CRI": "Costa Rica",
    "COL": "Colombia",
    "DOM": "Rep. Dominicana",
    "GTM": "Guatemala",
    "MEX": "México",
}


def _group_key(article: models.NewsArticle) -> str:
    return article.grupo_evento_id or f"solo:{article.id_noticia}"


def _has_indicator_relation(session: Session, member_ids: list[str]) -> bool:
    rel = session.exec(
        select(models.Relation).where(
            models.Relation.origen_tipo == "news",
            models.Relation.origen_id.in_(member_ids),  # type: ignore[attr-defined]
            models.Relation.destino_tipo == "indicator",
        )
    ).first()
    return rel is not None


def _score_news_groups(
    session: Session,
    modalidad: str = "tvn",
) -> list[dict[str, Any]]:
    """Score all news event groups in database."""
    articles = session.exec(select(models.NewsArticle)).all()
    if not articles:
        return []

    groups: dict[str, list[models.NewsArticle]] = {}
    for article in articles:
        groups.setdefault(_group_key(article), []).append(article)

    items = []
    for gid, members in groups.items():
        members_sorted = sorted(
            members,
            key=lambda a: (a.fecha_publicacion is None, a.fecha_publicacion, a.id_noticia),
        )
        title = members_sorted[0].titulo or ""
        published = members_sorted[0].fecha_publicacion
        member_dicts = [
            {"id_noticia": m.id_noticia, "agencia_primaria": m.agencia_primaria}
            for m in members
        ]
        label = label_group(member_dicts)
        member_ids = [m.id_noticia for m in members]
        has_ind = _has_indicator_relation(session, member_ids)
        titular_only = all((m.alcance_texto or "titular") == "titular" for m in members)

        result = scoring.score_topic(
            title=title,
            group_size=len(members),
            primary_sources=label["primary_sources"],
            published_at=published,
            modalidad=modalidad,
            has_indicator=has_ind,
            titular_only=titular_only,
            medio=members_sorted[0].medio or "",
            origen=members_sorted[0].origen or "",
        )

        items.append({
            "id": gid,
            "tipo": "news",
            "titulo": title,
            "modalidad": modalidad,
            "ids_fuente": member_ids,
            "group_size": len(members),
            "dedup": label,
            "fecha": published.isoformat() if published else None,
            "medio": members_sorted[0].medio or "",
            **result,
        })

    return items


def _score_indicators(
    session: Session,
    modalidad: str = "tvn",
) -> list[dict[str, Any]]:
    """Group indicator rows by series and score them deterministically."""
    indicators = session.exec(select(models.Indicator)).all()
    if not indicators:
        return []

    settings = get_settings()
    series_map: dict[tuple[str, str], list[models.Indicator]] = {}
    for ind in indicators:
        key = (ind.pais_iso3, ind.indicador_id)
        series_map.setdefault(key, []).append(ind)

    items = []
    for (pais, ind_code), obs_list in series_map.items():
        obs_sorted = sorted(obs_list, key=lambda o: o.anio, reverse=True)
        latest = obs_sorted[0]
        min_year = min(o.anio for o in obs_sorted)
        max_year = max(o.anio for o in obs_sorted)

        pais_nombre = COUNTRY_NAMES.get(pais, pais)
        ind_nombre = INDICATOR_NAMES.get(ind_code, ind_code)
        title = f"{ind_nombre} — {pais_nombre} ({min_year}–{max_year})"

        val_disp = f"{latest.valor:g} {latest.unidad or ''}".strip() if latest.valor is not None else "N/D"

        # Relevance scoring
        is_panama = (pais.upper() == "PAN")
        if is_panama:
            if modalidad == "banca":
                # High financial/macroeconomic priority
                r = 1.0 if ind_code in ("NY.GDP.MKTP.KD.ZG", "FP.CPI.TOTL.ZG", "SL.UEM.TOTL.ZS", "NE.EXP.GNFS.ZS") else 0.85
            else:
                # TVN news audience priority
                r = 0.95 if ind_code in ("FP.CPI.TOTL.ZG", "SL.UEM.TOTL.ZS", "IT.NET.USER.ZS", "SP.POP.TOTL") else 0.80
        else:
            # Regional benchmark context
            r = 0.70 if modalidad == "banca" else 0.60

        # Impact: Macro structural data
        imp = 0.85 if is_panama else 0.70

        # Urgency: Recency of the most recent year
        if max_year >= 2023:
            u = 0.80
        elif max_year >= 2020:
            u = 0.55
        else:
            u = 0.30

        # Novelty: Official statistical series
        nov = 0.85

        # Evidence: World Bank verified data series
        ev_score = 1.0

        components = {"R": r, "I": imp, "U": u, "N": nov, "E": ev_score}
        weights = {
            "R": settings.score_weight_relevance,
            "I": settings.score_weight_impact,
            "U": settings.score_weight_urgency,
            "N": settings.score_weight_novelty,
            "E": settings.score_weight_evidence,
        }
        total_p = round(sum(components[k] * weights[k] for k in components), 2)

        member_ids = [f"{o.pais_iso3}:{o.indicador_id}:{o.anio}" for o in obs_sorted]
        gid = f"ind:{pais}:{ind_code}"

        items.append({
            "id": gid,
            "tipo": "indicator",
            "titulo": title,
            "modalidad": modalidad,
            "ids_fuente": member_ids,
            "group_size": len(obs_sorted),
            "dedup": {
                "label": "official_series",
                "primary_sources": 1,
                "agency": "World Bank",
            },
            "P": total_p,
            "components": {k: round(v, 4) for k, v in components.items()},
            "weights": weights,
            "rules_version": scoring.RULES_VERSION,
            "band": scoring.band(total_p, rules_version=scoring.RULES_VERSION),
            "evidence_state": "suficiente",
            "latest_value": val_disp,
            "latest_year": max_year,
            "medio": "Banco Mundial (World Bank Open Data)",
            "fecha": f"{max_year}-01-01T00:00:00Z",
        })

    return items


def _score_events(
    session: Session,
    modalidad: str = "tvn",
) -> list[dict[str, Any]]:
    """Score USGS seismic events deterministically."""
    events = session.exec(select(models.GeoEvent)).all()
    if not events:
        return []

    settings = get_settings()
    items = []
    for ev in events:
        mag = ev.magnitude or 0.0
        place = ev.place or "Región Panamá"
        place_lower = place.lower()

        # Check proximity to Panama
        is_panama = any(t in place_lower for t in ("panam", "chiriqu", "bocas", "dari", "coiba", "azuer"))

        title = f"Sismo M{mag:.1f} — {place}"

        # Relevance
        if is_panama:
            r = 1.0 if modalidad == "tvn" else 0.75
        elif any(t in place_lower for t in ("costa rica", "colombia", "central america", "pacific")):
            r = 0.80 if modalidad == "tvn" else 0.60
        else:
            r = 0.50

        # Impact: scaled by magnitude (M6+ is severe, M4 is moderate)
        imp = min(1.0, 0.40 + (mag / 10.0))

        # Urgency: decay from event time
        u = scoring.urgency(ev.time)

        # Novelty
        nov = 0.85

        # Evidence: USGS instrumented sensor network
        ev_score = 1.0

        components = {"R": r, "I": imp, "U": u, "N": nov, "E": ev_score}
        weights = {
            "R": settings.score_weight_relevance,
            "I": settings.score_weight_impact,
            "U": settings.score_weight_urgency,
            "N": settings.score_weight_novelty,
            "E": settings.score_weight_evidence,
        }
        total_p = round(sum(components[k] * weights[k] for k in components), 2)

        gid = f"geo:{ev.event_id}"
        items.append({
            "id": gid,
            "tipo": "event",
            "titulo": title,
            "modalidad": modalidad,
            "ids_fuente": [ev.event_id],
            "group_size": 1,
            "dedup": {
                "label": "seismic_sensor",
                "primary_sources": 1,
                "agency": "USGS",
            },
            "P": total_p,
            "components": {k: round(v, 4) for k, v in components.items()},
            "weights": weights,
            "rules_version": scoring.RULES_VERSION,
            "band": scoring.band(total_p, rules_version=scoring.RULES_VERSION),
            "evidence_state": "suficiente",
            "magnitude": mag,
            "depth": ev.depth,
            "place": place,
            "medio": "USGS Earthquake Hazards Program",
            "fecha": ev.time.isoformat() if ev.time else None,
        })

    return items


def generate_inbox_topics(
    session: Session,
    modalidad: str = "tvn",
    limit: int = 500,
    tipo: str = "all",
) -> dict[str, Any]:
    """Generate prioritized inbox topics for the given modality and type filter."""
    tipo_norm = (tipo or "all").lower().strip()

    news_items = _score_news_groups(session, modalidad) if tipo_norm in ("all", "news") else []
    indicator_items = _score_indicators(session, modalidad) if tipo_norm in ("all", "indicator", "indicators") else []
    event_items = _score_events(session, modalidad) if tipo_norm in ("all", "event", "events") else []

    all_items = news_items + indicator_items + event_items
    all_items.sort(key=lambda it: (-it["P"], -it["components"]["U"], it["id"]))

    # Summary counts
    total_news = len(news_items) if tipo_norm == "all" else len(_score_news_groups(session, modalidad))
    total_ind = len(indicator_items) if tipo_norm == "all" else len(_score_indicators(session, modalidad))
    total_evt = len(event_items) if tipo_norm == "all" else len(_score_events(session, modalidad))

    return {
        "rules_version": scoring.RULES_VERSION,
        "modalidad": modalidad,
        "tipo": tipo_norm,
        "count": len(all_items),
        "total": len(all_items),
        "counts_by_type": {
            "total": total_news + total_ind + total_evt,
            "news": total_news,
            "indicator": total_ind,
            "event": total_evt,
        },
        "items": all_items[:limit],
    }


def generate_and_persist_inbox(session: Session) -> dict[str, Any]:
    """Precompute and persist the full multimodal inbox for all modalities."""
    try:
        processed_dir = resolve_data_path(Path(get_settings().data_dir) / "processed")
        processed_dir.mkdir(parents=True, exist_ok=True)
        inbox_file = processed_dir / "ranking_inbox.json"

        tvn_data = generate_inbox_topics(session, modalidad="tvn", limit=1000, tipo="all")
        banca_data = generate_inbox_topics(session, modalidad="banca", limit=1000, tipo="all")

        summary = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "rules_version": scoring.RULES_VERSION,
            "counts": tvn_data["counts_by_type"],
            "modalidades": {
                "tvn": {
                    "count": tvn_data["count"],
                    "items": tvn_data["items"],
                },
                "banca": {
                    "count": banca_data["count"],
                    "items": banca_data["items"],
                },
            },
        }

        inbox_file.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )
        logger.info(
            "Ranking inbox generated and persisted successfully: %d total topics (news=%d, ind=%d, ev=%d)",
            tvn_data["counts_by_type"]["total"],
            tvn_data["counts_by_type"]["news"],
            tvn_data["counts_by_type"]["indicator"],
            tvn_data["counts_by_type"]["event"],
        )
        return {
            "status": "success",
            "generated_at": summary["generated_at"],
            "counts": tvn_data["counts_by_type"],
        }
    except Exception as exc:
        logger.exception("Failed to generate and persist ranking inbox: %s", exc)
        return {
            "status": "error",
            "error": str(exc),
        }
