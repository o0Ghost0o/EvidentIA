"""Indexing: validated rows → parents/children → Qdrant (idempotent)."""

from __future__ import annotations

import logging
from typing import Optional

from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from evidentia.config import Settings, get_settings
from evidentia.retrieval import chunking
from evidentia.retrieval.embeddings import get_embeddings
from evidentia.retrieval.store import QdrantDocStore, delete_root_children, init_collections

logger = logging.getLogger(__name__)


def _index_parents(
    client: QdrantClient,
    parents: list,
    children_collection: str,
    parents_collection: str,
    embeddings=None,
    dimensions: int | None = None,
) -> int:
    if not parents:
        return 0
    embeddings = embeddings or get_embeddings()
    store = QdrantVectorStore(
        client=client, collection_name=children_collection, embedding=embeddings
    )
    docstore = QdrantDocStore(client, parents_collection)
    docstore.mset([(p.metadata["parent_id"], p) for p in parents])
    children = []
    for parent in parents:
        delete_root_children(client, children_collection, parent.metadata["root_id"])
        children.extend(chunking.split_children(parent))
    if children:
        store.add_documents(children)
    return len(parents)


def index_news(
    rows: list[dict],
    client: Optional[QdrantClient] = None,
    settings: Optional[Settings] = None,
    embeddings=None,
    dimensions: int | None = None,
) -> int:
    """Index validated news rows; returns parents written."""
    from evidentia.retrieval.store import get_qdrant_client

    cfg = settings or get_settings()
    client = client or get_qdrant_client(cfg)
    init_collections(client, cfg, dimensions=dimensions)
    parents = [chunking.build_news_parent(r) for r in rows]
    n = _index_parents(
        client, parents,
        cfg.qdrant_news_children_collection, cfg.qdrant_news_parents_collection,
        embeddings=embeddings, dimensions=dimensions,
    )
    logger.info("Indexed %d news parents", n)
    return n


def index_indicators(
    rows: list[dict],
    client: Optional[QdrantClient] = None,
    settings: Optional[Settings] = None,
    embeddings=None,
    dimensions: int | None = None,
) -> int:
    """Index validated indicator rows; returns parents written."""
    from evidentia.retrieval.store import get_qdrant_client

    cfg = settings or get_settings()
    client = client or get_qdrant_client(cfg)
    init_collections(client, cfg, dimensions=dimensions)
    parents = [chunking.build_indicator_parent(r) for r in rows]
    n = _index_parents(
        client, parents,
        cfg.qdrant_indicator_children_collection, cfg.qdrant_indicator_parents_collection,
        embeddings=embeddings, dimensions=dimensions,
    )
    logger.info("Indexed %d indicator parents", n)
    return n
