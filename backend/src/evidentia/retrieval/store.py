"""Qdrant bootstrap and persistent parent docstore.

Collections (created idempotently):
  - evidentia_news_children      : news chunk embeddings (index A)
  - evidentia_news_parents       : payload-only parent news documents
  - evidentia_indicator_children : indicator chunk embeddings (index B)
  - evidentia_indicator_parents  : payload-only parent indicator documents

Parent records are Qdrant points with a deterministic UUID id, a dummy 1-d DOT
vector and a payload of ``{"key": ..., "doc_json": ...}`` — this keeps the whole
retrieval state inside Qdrant with no second store.
"""

from __future__ import annotations

import json
import uuid
from typing import Iterator, Optional, Sequence

from langchain_core.documents import Document
from langchain_core.stores import BaseStore
from qdrant_client import QdrantClient, models as qmodels

from evidentia.config import Settings, get_settings

# Payload path used to scope idempotent re-index deletes per root document.
_CHILD_ROOT_KEY = "metadata.root_id"


def _str_to_uuid(key: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, key))


def get_qdrant_client(settings: Optional[Settings] = None) -> QdrantClient:
    """Build a Qdrant client; ``qdrant_url=":memory:"`` selects local mode."""
    cfg = settings or get_settings()
    if cfg.qdrant_url == ":memory:":
        return QdrantClient(":memory:")
    return QdrantClient(url=cfg.qdrant_url)


def _ensure_vector_collection(
    client: QdrantClient, name: str, dimensions: int, existing: set[str]
) -> None:
    if name in existing:
        return
    client.create_collection(
        collection_name=name,
        vectors_config=qmodels.VectorParams(size=dimensions, distance=qmodels.Distance.COSINE),
        hnsw_config=qmodels.HnswConfigDiff(m=16, ef_construct=100),
    )


def _ensure_payload_collection(client: QdrantClient, name: str, existing: set[str]) -> None:
    if name in existing:
        return
    client.create_collection(
        collection_name=name,
        vectors_config=qmodels.VectorParams(size=1, distance=qmodels.Distance.DOT),
    )


def init_collections(
    client: QdrantClient,
    settings: Optional[Settings] = None,
    dimensions: int | None = None,
) -> None:
    """Create all retrieval collections idempotently (safe on every startup)."""
    cfg = settings or get_settings()
    dim = dimensions or cfg.embedding_dimensions
    existing = {c.name for c in client.get_collections().collections}
    _ensure_vector_collection(client, cfg.qdrant_news_children_collection, dim, existing)
    _ensure_vector_collection(client, cfg.qdrant_indicator_children_collection, dim, existing)
    _ensure_payload_collection(client, cfg.qdrant_news_parents_collection, existing)
    _ensure_payload_collection(client, cfg.qdrant_indicator_parents_collection, existing)
    for coll in (cfg.qdrant_news_children_collection, cfg.qdrant_indicator_children_collection):
        try:
            client.create_payload_index(
                collection_name=coll,
                field_name="metadata.root_id",
                field_schema=qmodels.PayloadSchemaType.KEYWORD,
            )
        except Exception:
            pass  # index already exists


class QdrantDocStore(BaseStore[str, Document]):
    """LangChain docstore backed by a payload-only Qdrant collection."""

    def __init__(self, client: QdrantClient, collection_name: str) -> None:
        self.client = client
        self.collection_name = collection_name

    def mget(self, keys: Sequence[str]) -> list[Document | None]:
        if not keys:
            return []
        points = self.client.retrieve(
            collection_name=self.collection_name,
            ids=[_str_to_uuid(k) for k in keys],
            with_payload=True,
        )
        by_key = {(p.payload or {}).get("key"): p for p in points}
        out: list[Document | None] = []
        for key in keys:
            point = by_key.get(key)
            if point is None:
                out.append(None)
                continue
            data = json.loads((point.payload or {})["doc_json"])
            out.append(Document(page_content=data["page_content"], metadata=data["metadata"]))
        return out

    def mset(self, key_value_pairs: Sequence[tuple[str, Document]]) -> None:
        if not key_value_pairs:
            return
        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                qmodels.PointStruct(
                    id=_str_to_uuid(key),
                    vector=[1.0],
                    payload={
                        "key": key,
                        "doc_json": json.dumps(
                            {"page_content": doc.page_content, "metadata": doc.metadata},
                            ensure_ascii=False,
                        ),
                    },
                )
                for key, doc in key_value_pairs
            ],
        )

    def mdelete(self, keys: Sequence[str]) -> None:
        if not keys:
            return
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=qmodels.PointIdsList(points=[_str_to_uuid(k) for k in keys]),
        )

    def yield_keys(self, prefix: Optional[str] = None) -> Iterator[str]:  # type: ignore[override]
        offset = None
        while True:
            points, offset = self.client.scroll(
                collection_name=self.collection_name,
                limit=256,
                offset=offset,
                with_payload=["key"],
            )
            for point in points:
                key = (point.payload or {}).get("key", "")
                if prefix is None or key.startswith(prefix):
                    yield key
            if offset is None:
                return


def delete_root_children(client: QdrantClient, collection: str, root_id: str) -> None:
    """Delete child chunks of one root document (idempotent re-index)."""
    client.delete(
        collection_name=collection,
        points_selector=qmodels.FilterSelector(
            filter=qmodels.Filter(
                must=[qmodels.FieldCondition(key=_CHILD_ROOT_KEY, match=qmodels.MatchValue(value=root_id))]
            )
        ),
    )
