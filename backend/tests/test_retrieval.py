"""Fase 3 tests: indexing + dual retrieval on in-memory Qdrant."""

from __future__ import annotations

import pytest
from qdrant_client import QdrantClient

from evidentia.retrieval import chunking, indexing
from evidentia.retrieval.embeddings import HashEmbeddings
from evidentia.retrieval.retriever import MultiRAGRetriever
from evidentia.retrieval.store import QdrantDocStore

DIM = 128

NEWS_ROWS = [
    {
        "id_noticia": "gdelt-aaa", "titulo": "Canal de Panamá amplía capacidad de tránsito",
        "url": "https://example.com/a", "medio": "Prensa", "idioma": "es",
        "fecha_publicacion": "2026-10-01T00:00:00Z", "tema": "logística",
        "origen": "gdelt", "alcance_texto": "titular", "agencia_primaria": "",
    },
    {
        "id_noticia": "tvn-bbb", "titulo": "Turismo en Bocas del Toro bate récord",
        "url": "https://example.com/b", "medio": "TVN", "idioma": "es",
        "fecha_publicacion": "2026-10-02T00:00:00Z", "tema": "turismo",
        "origen": "tvn", "alcance_texto": "titular", "agencia_primaria": "",
    },
]

IND_ROWS = [
    {
        "pais_iso3": "PAN", "indicador_id": "NY.GDP.MKTP.KD.ZG", "anio": 2024,
        "valor": 2.74, "unidad": "% anual", "fuente_url": "https://api.worldbank.org",
    },
    {
        "pais_iso3": "PAN", "indicador_id": "SL.UEM.TOTL.ZS", "anio": 2024,
        "valor": None, "unidad": "%", "fuente_url": "https://api.worldbank.org",
    },
]


@pytest.fixture()
def mem_client() -> QdrantClient:
    return QdrantClient(":memory:")


@pytest.fixture()
def embeddings() -> HashEmbeddings:
    return HashEmbeddings(dimensions=DIM)


def test_indicator_parent_rendering() -> None:
    with_value = chunking.build_indicator_parent(IND_ROWS[0])
    assert "Panamá" in with_value.page_content
    assert "2024" in with_value.page_content and "2.74" in with_value.page_content
    assert with_value.metadata["tipo"] == "indicator"
    missing = chunking.build_indicator_parent(IND_ROWS[1])
    assert "sin dato" in missing.page_content


def test_index_and_query_both_indexes(mem_client, embeddings) -> None:
    assert indexing.index_news(NEWS_ROWS, client=mem_client, embeddings=embeddings, dimensions=DIM) == 2
    assert indexing.index_indicators(IND_ROWS, client=mem_client, embeddings=embeddings, dimensions=DIM) == 2

    multi = MultiRAGRetriever(client=mem_client, embeddings=embeddings)
    res = multi.query("Canal de Panamá tránsito", k=2)
    assert res["news"], "news index should return the canal parent"
    assert res["news"][0].metadata["id_noticia"] == "gdelt-aaa"
    assert res["news"][0].metadata["tipo"] == "news"

    res = multi.query("Panamá crecimiento PIB 2024", k=2)
    assert res["indicators"], "indicator index should return the GDP parent"
    assert res["indicators"][0].metadata["indicador_id"] == "NY.GDP.MKTP.KD.ZG"


def test_reindex_is_idempotent(mem_client, embeddings) -> None:
    from evidentia.config import get_settings

    settings = get_settings()
    indexing.index_news(NEWS_ROWS, client=mem_client, embeddings=embeddings, dimensions=DIM)
    indexing.index_news(NEWS_ROWS, client=mem_client, embeddings=embeddings, dimensions=DIM)
    count = mem_client.count(
        collection_name=settings.qdrant_news_children_collection, exact=True
    ).count
    # 2 short titles → 1 child chunk each; re-index must not duplicate.
    assert count == 2


def test_parent_docstore_roundtrip(mem_client) -> None:
    from evidentia.config import get_settings
    from evidentia.retrieval.store import init_collections

    settings = get_settings()
    init_collections(mem_client, settings, dimensions=DIM)
    store = QdrantDocStore(mem_client, settings.qdrant_news_parents_collection)
    parent = chunking.build_news_parent(NEWS_ROWS[0])
    store.mset([(parent.metadata["parent_id"], parent)])
    fetched = store.mget([parent.metadata["parent_id"]])
    assert fetched[0] is not None
    assert fetched[0].metadata["url"] == "https://example.com/a"
    assert list(store.yield_keys(prefix="news:")) == [parent.metadata["parent_id"]]


def test_bm25_baseline_index_and_search() -> None:
    from evidentia.retrieval.baseline import BM25Index, tokenize

    tokens = tokenize("¿Qué se reporta sobre el Canal de Panamá?")
    assert "canal" in tokens
    assert "panamá" in tokens
    assert "de" not in tokens  # stopword removed

    index = BM25Index()
    docs = [
        {"id": "doc1", "text": "Canal de Panamá anuncia aumento de calado"},
        {"id": "doc2", "text": "Presupuesto de la nación aprobado por la Asamblea"},
        {"id": "doc3", "text": "Turismo en las playas de Bocas del Toro"},
    ]
    index.index(docs)
    results = index.search("aumento de calado en el Canal", top_k=2)
    assert len(results) >= 1
    assert results[0][0].doc_id == "doc1"
    assert results[0][1] > 0.0


def test_baseline_benchmark_evaluation_contract() -> None:
    from evidentia.retrieval.baseline import evaluate_benchmark

    res = evaluate_benchmark(benchmark_path="data/benchmark.jsonl", seed_dir="data/seed", top_k=5)
    assert res["benchmark_total_queries"] == 60
    assert res["sustentadas_count"] == 30
    assert res["bm25"]["hit_at_5"] > 0.8
    assert res["semantic_multirag"]["abstention_rate"] == 1.0
    assert "donde_mejora_ia" in res["conclusions"]
    assert "donde_no_aporta_ia" in res["conclusions"]

