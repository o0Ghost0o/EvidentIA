"""Evidence-tree queries over the provenance graph."""

from __future__ import annotations

from fastapi import APIRouter, Query

from evidentia.db import SessionDep
from evidentia.graph.graph_service import evidence_tree

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.get("/tree")
def get_tree(
    session: SessionDep,
    tipo: str = Query(pattern="^(news|indicator|event|entity)$"),
    id: str = Query(min_length=1),
    depth: int = Query(default=2, ge=1, le=3),
) -> dict:
    """Return the neighbourhood of any graph node as nodes + typed edges."""
    return evidence_tree(session, tipo, id, depth=depth)
