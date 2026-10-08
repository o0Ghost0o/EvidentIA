"""Prioritised inbox: deterministic ranking over news event groups, indicators and events."""

from __future__ import annotations

from fastapi import APIRouter, Query

from evidentia.db import SessionDep
from evidentia.scoring.ranking_service import generate_inbox_topics

router = APIRouter(prefix="/ranking", tags=["ranking"])


@router.get("")
def get_ranking(
    session: SessionDep,
    modalidad: str = Query(default="tvn", pattern="^(tvn|banca)$"),
    limit: int = Query(default=500, ge=1, le=1000),
    tipo: str = Query(default="all", pattern="^(all|news|indicator|indicators|event|events)$"),
) -> dict:
    """Rank multimodal items (news, indicators, events) by attention score (P desc, U desc, id asc)."""
    return generate_inbox_topics(
        session=session,
        modalidad=modalidad,
        limit=limit,
        tipo=tipo,
    )
