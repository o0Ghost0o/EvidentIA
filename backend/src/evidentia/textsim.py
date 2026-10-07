"""Shared title tokenisation and Jaccard similarity.

Used by both news deduplication (ingestion) and event grouping (graph) so a
single notion of "similar headline" governs the pipeline. Digit-only tokens are
dropped so numeric variants of one story still match (their differences surface
later as contradictions, not as separate events).
"""

from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[a-záéíóúñü0-9]+", re.IGNORECASE)
_STOPWORDS = frozenset({
    "de", "la", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un",
    "para", "con", "no", "una", "the", "of", "to", "in", "and", "for", "on",
})


def title_tokens(title: str) -> set[str]:
    """Lowercased content tokens of a headline, stopwords and digits removed."""
    return {
        t.lower() for t in _TOKEN_RE.findall(title or "")
        if not t.isdigit()
    } - _STOPWORDS


def jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard overlap of two token sets; 0.0 when either is empty."""
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)
