"""Parent-child retrievers and the dual-index MultiRAG retriever.

Index A (news) and index B (indicators) are searched independently and merged
by the caller: each parent carries ``tipo`` plus its trace fields so scoring
and generation can cite ``[id_fuente:campo]`` without extra lookups.
"""

from __future__ import annotations

from typing import Optional

from langchain_core.callbacks.manager import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from evidentia.config import Settings, get_settings
from evidentia.retrieval.embeddings import get_embeddings
from evidentia.retrieval.store import QdrantDocStore

PARENT_ID_KEY = "doc_id"


class ParentChildRetriever(BaseRetriever):
    """Search child chunks, return deduplicated parent Documents."""

    vector_store: QdrantVectorStore
    docstore: QdrantDocStore
    id_key: str = PARENT_ID_KEY
    child_k: int = 20

    model_config = {"arbitrary_types_allowed": True}

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> list[Document]:
        children = self.vector_store.similarity_search(query, k=self.child_k)
        seen: set[str] = set()
        parent_ids: list[str] = []
        for child in children:
            pid = child.metadata.get(self.id_key)
            if pid and pid not in seen:
                seen.add(pid)
                parent_ids.append(pid)
        if not parent_ids:
            return []
        return [doc for doc in self.docstore.mget(parent_ids) if doc is not None]


class MultiRAGRetriever:
    """Dual-index retriever: news (A) + indicators (B)."""

    def __init__(
        self,
        client: QdrantClient,
        settings: Optional[Settings] = None,
        embeddings=None,
        dimensions: int | None = None,
    ) -> None:
        cfg = settings or get_settings()
        embeddings = embeddings or get_embeddings()
        self.top_k = cfg.retrieval_top_k
        self.news = ParentChildRetriever(
            vector_store=QdrantVectorStore(
                client=client,
                collection_name=cfg.qdrant_news_children_collection,
                embedding=embeddings,
            ),
            docstore=QdrantDocStore(client, cfg.qdrant_news_parents_collection),
        )
        self.indicators = ParentChildRetriever(
            vector_store=QdrantVectorStore(
                client=client,
                collection_name=cfg.qdrant_indicator_children_collection,
                embedding=embeddings,
            ),
            docstore=QdrantDocStore(client, cfg.qdrant_indicator_parents_collection),
        )

    def query(self, text: str, k: int | None = None) -> dict[str, list[Document]]:
        """Search both indexes; returns parents tagged by ``tipo``."""
        k = k or self.top_k
        news_docs = self.news.invoke(text)[:k]
        indicator_docs = self.indicators.invoke(text)[:k]
        return {"news": news_docs, "indicators": indicator_docs}
