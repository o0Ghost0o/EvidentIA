"""Fase 3 tests: agency detection, event grouping, evidence trees."""

from __future__ import annotations

from sqlmodel import Session

from evidentia import models
from evidentia.db import get_engine, init_db
from evidentia.graph import entities as ent
from evidentia.graph import relations as rel_mod
from evidentia.graph.graph_service import (
    count_primary_sources,
    evidence_tree,
    persist_graph,
)


def _articles() -> list[dict]:
    return [
        {"id_noticia": "a1", "titulo": "EFE.- Panamá aprueba ampliación del Canal",
         "url": "https://m1.example/a1", "medio": "Medio Uno"},
        {"id_noticia": "a2", "titulo": "Panamá aprueba ampliación del Canal de Panamá",
         "url": "https://www.efe.com/a2", "medio": "Diario EFE"},
        {"id_noticia": "a3", "titulo": "Panamá aprueba ampliación del Canal, informa prensa local",
         "url": "https://local.example/a3", "medio": "La Local"},
    ]


def test_detect_agency() -> None:
    assert ent.detect_agency("EFE", "https://x.example/1", "Algo") == "EFE"
    assert ent.detect_agency("Foo", "https://www.reuters.com/x", "Algo") == "Reuters"
    assert ent.detect_agency("Foo", "https://x.example/1", "AFP.- Algo pasó") == "AFP"
    assert ent.detect_agency("La Local", "https://local.example/1", "Algo pasó") is None


def test_grouping_repetition_vs_corroboration() -> None:
    enriched, relations = rel_mod.build_article_relations(_articles())
    assert enriched[0]["agencia_primaria"] == "EFE"
    assert enriched[1]["agencia_primaria"] == "EFE"
    assert enriched[2]["agencia_primaria"] is None
    # All three share one event group.
    groups = {a.get("grupo_evento_id") for a in enriched}
    assert len(groups) == 1 and None not in groups
    kinds = [r["tipo"] for r in relations]
    assert kinds.count("same_event") == 3  # C(3,2)
    assert kinds.count("source_of") == 2  # the two EFE replicas
    # a3 (independent outlet, no agency) corroborates each replica.
    assert kinds.count("corroborates") == 2
    # The two EFE replicas do NOT corroborate each other.
    pairs = {(r["origen_id"], r["destino_id"]) for r in relations if r["tipo"] == "corroborates"}
    assert ("a1", "a2") not in pairs


def test_numeric_variants_group_together() -> None:
    """Digit-only tokens are ignored so 2.7% vs 5.1% variants group (T05)."""
    assert rel_mod.title_tokens("Crece 2.7% en 2024") == {"crece"}
    articles = [
        {"id_noticia": "n1", "titulo": "Panamá crece 2.7% en 2024, cifra oficial",
         "url": "https://a.example/1", "medio": "A"},
        {"id_noticia": "n2", "titulo": "Panamá crece 5.1% en 2024, cifra oficial",
         "url": "https://b.example/1", "medio": "B"},
    ]
    groups = rel_mod.group_articles(articles)
    assert len(groups) == 1


def test_persist_tree_and_primary_count() -> None:
    init_db()
    with Session(get_engine()) as session:
        for art in _articles():
            session.add(models.NewsArticle(
                id_noticia=art["id_noticia"], titulo=art["titulo"],
                url=art["url"], medio=art["medio"],
            ))
        session.commit()
        enriched, relations = rel_mod.build_article_relations(_articles())
        counts = persist_graph(session, enriched, relations)
        assert counts["relations"] >= len(relations)

        tree = evidence_tree(session, "news", "a1", depth=2)
        node_ids = {(n["tipo"], n["id"]) for n in tree["nodes"]}
        assert ("news", "a1") in node_ids and ("news", "a3") in node_ids
        edge_kinds = {e["tipo"] for e in tree["edges"]}
        assert {"same_event", "source_of", "corroborates"} <= edge_kinds

        # CU-03: two EFE replicas + one independent outlet = 2 sources.
        assert count_primary_sources(session, ["a1", "a2", "a3"]) == 2
