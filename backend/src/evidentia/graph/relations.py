"""Relation builders: event grouping, provenance and corroboration.

Rules (prototype-grade, documented for the baseline comparison):
  - Two articles join the same event group when their title token-Jaccard is
    >= GROUP_JACCARD, or when they share a detected wire agency and their
    Jaccard is >= AGENCY_JACCARD (lower bar: same wire, lightly re-titled).
  - ``same_event`` edges link group members; ``source_of`` links each replica
    to its agency entity; ``corroborates`` links members published by different
    outlets with no shared agency (independent corroboration, CU-03).
  - ``contradicts`` edges are stored and served by the tree service, but their
    detection rule lands with claim extraction (Fase 4).
"""

from __future__ import annotations

import hashlib
import re

from evidentia.graph import entities as ent
from evidentia.scoring.deduplication import find_numeric_contradictions

GROUP_JACCARD = 0.45
AGENCY_JACCARD = 0.30

_TOKEN_RE = re.compile(r"[a-záéíóúñü0-9]+", re.IGNORECASE)
_STOPWORDS = frozenset({
    "de", "la", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un",
    "para", "con", "no", "una", "the", "of", "to", "in", "and", "for", "on",
})

REL_MENTIONS = "mentions"
REL_SAME_EVENT = "same_event"
REL_SOURCE_OF = "source_of"
REL_CONTRADICTS = "contradicts"
REL_CORROBORATES = "corroborates"


def title_tokens(title: str) -> set[str]:
    # Digit-only tokens are dropped: numeric variants of one story must group
    # together so their differences can surface as contradictions.
    return {
        t.lower() for t in _TOKEN_RE.findall(title or "")
        if not t.isdigit()
    } - _STOPWORDS


def _jaccard_value(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def group_id_for(members: list[str]) -> str:
    """Deterministic group id from sorted member ids."""
    digest = hashlib.sha256("|".join(sorted(members)).encode()).hexdigest()[:12]
    return f"evt-{digest}"


def group_articles(articles: list[dict]) -> list[list[dict]]:
    """Greedy single-link clustering of articles into event groups."""
    groups: list[list[dict]] = []
    token_cache = {id(a): title_tokens(a.get("titulo") or "") for a in articles}
    for article in articles:
        placed = False
        for group in groups:
            for member in group:
                same_agency = (article.get("agencia_primaria") or "") and (
                    article.get("agencia_primaria") == member.get("agencia_primaria")
                )
                score = _jaccard_value(token_cache[id(article)], token_cache[id(member)])
                bar = AGENCY_JACCARD if same_agency else GROUP_JACCARD
                if score >= bar:
                    group.append(article)
                    placed = True
                    break
            if placed:
                break
        if not placed:
            groups.append([article])
    return groups


def build_article_relations(articles: list[dict]) -> tuple[list[dict], list[dict]]:
    """Enrich articles (agency, group) and emit news-level relations.

    Returns (enriched_articles, relations) where each relation is a dict with
    origen_tipo/origen_id/destino_tipo/destino_id/tipo/peso keys.
    """
    for article in articles:
        article["agencia_primaria"] = ent.detect_agency(
            article.get("medio") or "", article.get("url") or "", article.get("titulo") or ""
        )

    relations: list[dict] = []
    for group in group_articles(articles):
        if len(group) < 2:
            continue
        gid = group_id_for([a["id_noticia"] for a in group])
        for article in group:
            article["grupo_evento_id"] = gid
        for i, left in enumerate(group):
            for right in group[i + 1 :]:
                relations.append({
                    "origen_tipo": "news", "origen_id": left["id_noticia"],
                    "destino_tipo": "news", "destino_id": right["id_noticia"],
                    "tipo": REL_SAME_EVENT, "peso": 1.0,
                })
                left_ag, right_ag = left.get("agencia_primaria"), right.get("agencia_primaria")
                if (left.get("medio") != right.get("medio")) and not (
                    left_ag and left_ag == right_ag
                ):
                    relations.append({
                        "origen_tipo": "news", "origen_id": left["id_noticia"],
                        "destino_tipo": "news", "destino_id": right["id_noticia"],
                        "tipo": REL_CORROBORATES, "peso": 0.8,
                    })

    for group in group_articles(articles):
        if len(group) < 2:
            continue
        for contra in find_numeric_contradictions(group):
            relations.append({
                "origen_tipo": "news", "origen_id": contra["a_id"],
                "destino_tipo": "news", "destino_id": contra["b_id"],
                "tipo": REL_CONTRADICTS, "peso": 0.9,
            })

    for article in articles:
        agency = article.get("agencia_primaria")
        if agency:
            relations.append({
                "origen_tipo": "news", "origen_id": article["id_noticia"],
                "destino_tipo": "entity", "destino_id": f"agency:{agency}",
                "tipo": REL_SOURCE_OF, "peso": 1.0,
            })
    return articles, relations


def build_mention_relations(
    articles: list[dict], entity_lookup: dict[str, str]
) -> list[dict]:
    """Emit ``mentions`` edges from NER over titles (entity_lookup: normalized→id)."""
    relations: list[dict] = []
    for article in articles:
        for name, _tipo in ent.extract_entities(article.get("titulo") or ""):
            eid = entity_lookup.get(ent.normalize_entity(name))
            if eid:
                relations.append({
                    "origen_tipo": "news", "origen_id": article["id_noticia"],
                    "destino_tipo": "entity", "destino_id": eid,
                    "tipo": REL_MENTIONS, "peso": 0.7,
                })
    return relations
