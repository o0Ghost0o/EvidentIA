"""Entity extraction (spaCy Spanish NER + regex fallback) and agency detection."""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

SPACY_MODEL = "es_core_news_sm"

# Wire agencies whose replicas count as ONE primary provenance (CU-03).
AGENCIES = {
    "efe": "EFE",
    "reuters": "Reuters",
    "afp": "AFP",
    "associated press": "AP",
    "\bap\b": "AP",
    "dpa": "DPA",
    "xinhua": "Xinhua",
    "europa press": "Europa Press",
}

_AGENCY_TITLE_RE = re.compile(
    r"^\s*(efe|reuters|afp|ap|dpa|xinhua)[\s:.\-|–—]+", re.IGNORECASE
)
_CAPITALIZED_RE = re.compile(r"\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){0,3}\b")

_nlp = None
_nlp_failed = False


def _load_nlp():  # type: ignore[no-untyped-def]
    global _nlp, _nlp_failed
    if _nlp is None and not _nlp_failed:
        try:
            import spacy

            _nlp = spacy.load(SPACY_MODEL)
        except Exception as exc:
            _nlp_failed = True
            logger.warning("spaCy model %s unavailable (%s) — regex fallback", SPACY_MODEL, exc)
    return _nlp


def detect_agency(medio: str = "", url: str = "", titulo: str = "") -> str | None:
    """Return the canonical agency name when the piece replicates a wire."""
    haystack = f"{medio} {url}".lower()
    for token, canonical in AGENCIES.items():
        if token.startswith("\\b"):
            if re.search(token, haystack):
                return canonical
        elif token in haystack:
            return canonical
    match = _AGENCY_TITLE_RE.match(titulo or "")
    if match:
        return AGENCIES.get(match.group(1).lower(), match.group(1).upper())
    return None


def extract_entities(text: str, max_entities: int = 25) -> list[tuple[str, str]]:
    """Extract (name, type) entities; regex fallback when spaCy is unavailable."""
    if not text or not text.strip():
        return []
    nlp = _load_nlp()
    if nlp is not None:
        try:
            doc = nlp(text[:5000])
            out = []
            for ent in doc.ents:
                if ent.label_ in ("PER", "ORG", "LOC", "MISC"):
                    out.append((ent.text.strip(), ent.label_))
            return out[:max_entities]
        except Exception as exc:
            logger.warning("spaCy NER failed (%s) — regex fallback", exc)
    found: list[tuple[str, str]] = []
    seen: set[str] = set()
    for match in _CAPITALIZED_RE.finditer(text):
        name = match.group(0).strip()
        if len(name) < 3 or name.lower() in seen:
            continue
        seen.add(name.lower())
        found.append((name, "MISC"))
        if len(found) >= max_entities:
            break
    return found


def normalize_entity(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())
