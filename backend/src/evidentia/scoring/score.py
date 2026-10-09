"""Deterministic attention scoring (rules v1).

``P = 30R + 25I + 20U + 15N + 10E`` with every component normalised to 0–1 by
documented rules. Bands: low [0,40), medium [40,70), high [70,100]. Ties break
by urgency, then by id. This is an ordering tool — not a truth probability.

Component rules v1 (heuristic baseline, fully reproducible):
  R relevance  1.0 title names Panamá + a modality theme; 0.7 one of them;
               0.3 neither.
  I impact     min(1, 0.25 + 0.25*log2(1 + group_size) + 0.25*has_indicator).
  U urgency    recency decay: 1.0 (<24h) → 0.0 (≥30d); unknown date → 0.3.
  N novelty    1/sqrt(group_size): the first story scores 1, replicas less.
  E evidence   min(1, 0.4*primary_sources + 0.2*has_indicator).

Evidence state (independent of the score):
  insuficiente  0 sources, or 1 titular-only source.
  parcial       1 source with extracto/completo.
  suficiente    ≥2 primary provenances, or 1 source + 1 indicator.
A high P with insuficiente evidence means "investigate", never "publish".
"""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone

from evidentia.config import get_settings

RULES_VERSION = "v1.2"

PANAMA_RE = re.compile(r"panam|coclé|colón|chiriquí|bocas|darién|veraguas|herrera|santos|azuerro", re.IGNORECASE)

PANAMA_MEDIA_TOKENS = {
    "tvn", "tvn-2", "tvn noticias", "la prensa", "crítica", "critica",
    "panamá américa", "panama america", "mi diario", "metro libre",
    "radio panamá", "rpc", "telemetro", "anpanama", "sertv", "en segundos",
}

TVN_THEMES = {
    "economía", "economia", "canal", "logística", "logistica", "turismo",
    "servicios", "públicos", "publicos", "naturales", "sismo", "inundación",
    "regulación", "regulacion", "educación", "salud", "transporte", "presupuesto",
}
BANCA_THEMES = {
    "economía", "economia", "pib", "inflación", "inflacion", "desempleo",
    "exportaciones", "logística", "logistica", "canal", "turismo", "regulación",
    "regulacion", "bancos", "crédito", "tasa", "presupuesto",
}

# Bands v1.2: recalibrated with expanded corpus (150+ news) for balanced distribution
BAND_LOW_V12 = (0.0, 55.0)
BAND_MEDIUM_V12 = (55.0, 75.0)
BAND_HIGH_V12 = (75.0, 100.0)

# Legacy Bands v1
BAND_LOW_V1 = (0.0, 40.0)
BAND_MEDIUM_V1 = (40.0, 70.0)
BAND_HIGH_V1 = (70.0, 100.0)


def is_panama_outlet(medio: str = "", origen: str = "") -> bool:
    """Check if outlet or source origin is recognized as Panamanian."""
    m = (medio or "").lower()
    o = (origen or "").lower()
    return any(tok in m or tok in o for tok in PANAMA_MEDIA_TOKENS) or bool(PANAMA_RE.search(m) or PANAMA_RE.search(o))


def _themes_for(modalidad: str) -> set[str]:
    return BANCA_THEMES if modalidad == "banca" else TVN_THEMES


def relevance(
    title: str,
    modalidad: str = "tvn",
    medio: str = "",
    origen: str = "",
    rules_version: str = RULES_VERSION,
) -> float:
    hay = (title or "").lower()
    panama = bool(PANAMA_RE.search(hay))
    theme = any(t in hay for t in _themes_for(modalidad))
    is_local = is_panama_outlet(medio, origen) if rules_version >= "v1.2" else False

    if is_local:
        # Rules v1.2: local Panamanian outlets have implicit national context
        if panama and theme:
            return 1.0
        if panama or theme:
            return 0.85
        return 0.6  # baseline national relevance instead of collapsing to 0.3
    else:
        if panama and theme:
            return 1.0
        if panama or theme:
            return 0.7
        return 0.3


def impact(group_size: int, has_indicator: bool = False) -> float:
    return min(1.0, 0.25 + 0.25 * math.log2(1 + max(group_size, 1)) + (0.25 if has_indicator else 0.0))


def urgency(published_at: datetime | None, now: datetime | None = None) -> float:
    if published_at is None:
        return 0.3
    now = now or datetime.now(timezone.utc)
    if published_at.tzinfo is None:
        published_at = published_at.replace(tzinfo=timezone.utc)
    age_hours = max((now - published_at).total_seconds() / 3600.0, 0.0)
    if age_hours <= 24:
        return 1.0
    if age_hours >= 30 * 24:
        return 0.0
    return 1.0 - (age_hours - 24) / (30 * 24 - 24)


def novelty(group_size: int) -> float:
    return 1.0 / math.sqrt(max(group_size, 1))


def evidence(primary_sources: int, has_indicator: bool = False) -> float:
    return min(1.0, 0.4 * max(primary_sources, 0) + (0.2 if has_indicator else 0.0))


def evidence_state(
    primary_sources: int, has_indicator: bool = False, titular_only: bool = True
) -> str:
    """insuficiente | parcial | suficiente (independent of P)."""
    if primary_sources >= 2 or (primary_sources >= 1 and has_indicator):
        return "suficiente"
    if primary_sources == 1:
        return "insuficiente" if titular_only else "parcial"
    return "insuficiente"


def band(score: float, rules_version: str = RULES_VERSION) -> str:
    threshold_low, threshold_high = (
        (BAND_MEDIUM_V1[0], BAND_HIGH_V1[0])
        if rules_version == "v1"
        else (BAND_MEDIUM_V12[0], BAND_HIGH_V12[0])
    )
    if score < threshold_low:
        return "bajo"
    if score < threshold_high:
        return "medio"
    return "alto"


def score_topic(
    title: str,
    group_size: int = 1,
    primary_sources: int = 1,
    published_at: datetime | None = None,
    modalidad: str = "tvn",
    has_indicator: bool = False,
    titular_only: bool = True,
    medio: str = "",
    origen: str = "",
    rules_version: str = RULES_VERSION,
) -> dict:
    """Score one topic/group; returns P, components, band and evidence state."""
    settings = get_settings()
    components = {
        "R": relevance(title, modalidad, medio=medio, origen=origen, rules_version=rules_version),
        "I": impact(group_size, has_indicator),
        "U": urgency(published_at),
        "N": novelty(group_size),
        "E": evidence(primary_sources, has_indicator),
    }
    weights = {
        "R": settings.score_weight_relevance,
        "I": settings.score_weight_impact,
        "U": settings.score_weight_urgency,
        "N": settings.score_weight_novelty,
        "E": settings.score_weight_evidence,
    }
    total = round(sum(components[k] * weights[k] for k in components), 2)
    return {
        "P": total,
        "components": {k: round(v, 4) for k, v in components.items()},
        "weights": weights,
        "rules_version": rules_version,
        "band": band(total, rules_version=rules_version),
        "evidence_state": evidence_state(primary_sources, has_indicator, titular_only),
    }
