"""Prioritised inbox: deterministic ranking over news event groups."""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlmodel import Session, select

from evidentia import models
from evidentia.db import SessionDep
from evidentia.scoring import score as scoring
from evidentia.scoring.deduplication import label_group

router = APIRouter(prefix="/ranking", tags=["ranking"])


def _group_key(article: models.NewsArticle) -> str:
    return article.grupo_evento_id or f"solo:{article.id_noticia}"


def _has_indicator(session: Session, member_ids: list[str]) -> bool:
    rel = session.exec(
        select(models.Relation).where(
            models.Relation.origen_tipo == "news",
            models.Relation.origen_id.in_(member_ids),  # type: ignore[attr-defined]
            models.Relation.destino_tipo == "indicator",
        )
    ).first()
    return rel is not None


@router.get("")
def get_ranking(
    session: SessionDep,
    modalidad: str = Query(default="tvn", pattern="^(tvn|banca)$"),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    """Rank event groups by attention score (P desc, U desc, id asc)."""
    articles = session.exec(select(models.NewsArticle)).all()
    groups: dict[str, list[models.NewsArticle]] = {}
    for article in articles:
        groups.setdefault(_group_key(article), []).append(article)

    items = []
    for gid, members in groups.items():
        members_sorted = sorted(members, key=lambda a: (a.fecha_publicacion is None, a.fecha_publicacion, a.id_noticia))
        title = members_sorted[0].titulo or ""
        published = members_sorted[0].fecha_publicacion
        member_dicts = [
            {"id_noticia": m.id_noticia, "agencia_primaria": m.agencia_primaria}
            for m in members
        ]
        label = label_group(member_dicts)
        member_ids = [m.id_noticia for m in members]
        has_indicator = _has_indicator(session, member_ids)
        titular_only = all((m.alcance_texto or "titular") == "titular" for m in members)
        result = scoring.score_topic(
            title=title,
            group_size=len(members),
            primary_sources=label["primary_sources"],
            published_at=published,
            modalidad=modalidad,
            has_indicator=has_indicator,
            titular_only=titular_only,
            medio=members_sorted[0].medio or "",
            origen=members_sorted[0].origen or "",
        )
        items.append({
            "id": gid,
            "titulo": title,
            "modalidad": modalidad,
            "ids_fuente": member_ids,
            "group_size": len(members),
            "dedup": label,
            **result,
        })

    items.sort(key=lambda it: (-it["P"], -it["components"]["U"], it["id"]))
    return {
        "rules_version": scoring.RULES_VERSION,
        "count": len(items),
        "items": items[:limit],
    }
