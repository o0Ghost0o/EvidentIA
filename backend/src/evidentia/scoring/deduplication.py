"""Group labels (repetition vs corroboration) + numeric contradiction checks.

Labels:
  single                    one article, no group.
  repetition                every member replicates the same wire agency.
  independent_corroboration ≥2 distinct provenances in the group.
  mixed                     group without agency signal (default informative label).

Contradictions (heuristic, documented): two same-group articles contradict when
both state numbers with the same unit (%, USD, MW, …) but different values.
"""

from __future__ import annotations

import re

_NUMBER_RE = re.compile(r"(\d[\d.,]*)\s*(%|por ciento|millones|millone|mdd|usd|dólares|dolares|balboas|mw|gw|empleos|hectáreas|km|casos|muertos|heridos)?", re.IGNORECASE)


def _parse_number(text: str) -> float | None:
    cleaned = text.replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def numeric_claims(title: str) -> list[tuple[float, str]]:
    """Extract (value, unit) numeric claims from a title."""
    claims = []
    for match in _NUMBER_RE.finditer(title or ""):
        value = _parse_number(match.group(1))
        if value is None:
            continue
        unit = (match.group(2) or "").lower()
        claims.append((value, unit))
    return claims


def find_numeric_contradictions(members: list[dict]) -> list[dict]:
    """Pairwise contradiction check inside one event group."""
    out = []
    claims = [(m, numeric_claims(m.get("titulo") or "")) for m in members]
    for i, (left, left_claims) in enumerate(claims):
        for right, right_claims in claims[i + 1 :]:
            for lval, lunit in left_claims:
                for rval, runit in right_claims:
                    if lunit == runit and abs(lval - rval) > 1e-9:
                        out.append({
                            "a_id": left["id_noticia"], "b_id": right["id_noticia"],
                            "a_value": lval, "b_value": rval, "unit": lunit or "adimensional",
                            "detail": f"{lval} vs {rval} {lunit or ''} en el mismo evento".strip(),
                        })
    return out


def label_group(members: list[dict]) -> dict:
    """Label an event group and count its primary provenances."""
    if len(members) <= 1:
        return {"label": "single", "primary_sources": min(len(members), 1), "agency": None}
    agencies = {m.get("agencia_primaria") for m in members if m.get("agencia_primaria")}
    independents = sum(1 for m in members if not m.get("agencia_primaria"))
    primary_sources = len(agencies) + independents
    if agencies and independents == 0 and len(agencies) == 1:
        return {
            "label": "repetition",
            "primary_sources": 1,
            "agency": next(iter(agencies)),
        }
    if primary_sources >= 2:
        return {"label": "independent_corroboration", "primary_sources": primary_sources, "agency": None}
    return {"label": "mixed", "primary_sources": primary_sources, "agency": None}
