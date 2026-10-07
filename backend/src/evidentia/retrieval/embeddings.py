"""Embeddings: local FastEmbed (production) and hashing (tests/fallback)."""

from __future__ import annotations

import hashlib
import math
import re

from langchain_core.embeddings import Embeddings

_TOKEN_RE = re.compile(r"[a-záéíóúñü0-9]+", re.IGNORECASE)


class FastEmbedEmbeddings(Embeddings):
    """Local embeddings via fastembed (ONNX runtime, no API key).

    The underlying ``fastembed.TextEmbedding`` loads lazily on first use so
    imports stay cheap. ``embed_query`` uses ``query_embed`` (bge retrieval
    instruction prefix); documents embed plain.
    """

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model = None

    def _load(self):  # type: ignore[no-untyped-def]
        if self._model is None:
            from fastembed import TextEmbedding

            self._model = TextEmbedding(model_name=self.model_name)
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [v.tolist() for v in self._load().embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return next(iter(self._load().query_embed(text))).tolist()


class HashEmbeddings(Embeddings):
    """Deterministic char-trigram hashing embeddings (tests / offline fallback).

    Not a quality retrieval model — it only guarantees determinism and rough
    textual similarity so the retrieval plumbing is testable without model
    downloads.
    """

    def __init__(self, dimensions: int = 128) -> None:
        self.dimensions = dimensions

    def _embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dimensions
        tokens = _TOKEN_RE.findall(text.lower())
        for tok in tokens:
            grams = [tok[i : i + 3] for i in range(max(len(tok) - 2, 1))] or [tok]
            for gram in grams:
                h = int(hashlib.md5(gram.encode()).hexdigest(), 16)
                vec[h % self.dimensions] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def get_embeddings(model_name: str = "", dimensions: int = 0) -> Embeddings:
    """Resolve the configured embeddings; ``hash`` selects HashEmbeddings."""
    from evidentia.config import get_settings

    settings = get_settings()
    model_name = model_name or settings.embedding_model
    if model_name == "hash":
        return HashEmbeddings(dimensions=dimensions or 128)
    return FastEmbedEmbeddings(model_name=model_name)
