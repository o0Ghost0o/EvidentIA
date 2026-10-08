"""Row validators for the data contract.

Policy (challenge T01): invalid dates and nulls never block the load — rows are
kept with the offending field nulled and the problem recorded; only rows
missing their identity (title/URL, country/indicator/year, event id) are
dropped. Duplicates by URL / natural key are collapsed, keeping the first.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urlparse

from evidentia.textsim import jaccard, title_tokens

# Near-duplicate headlines are collapsed above this Jaccard. The bar is high on
# purpose: it removes re-posts of the same story (slightly re-titled) without
# merging genuinely different news. Looser event grouping lives in graph layer.
TITLE_DEDUP_JACCARD = 0.85


@dataclass
class ValidationResult:
    valid: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    dropped: int = 0


def parse_datetime(value: object) -> datetime | None:
    """Best-effort ISO 8601 parse; returns None when unparseable."""
    if value is None or isinstance(value, datetime):
        if isinstance(value, datetime) and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value  # type: ignore[return-value]
    if isinstance(value, str) and value.strip():
        text = value.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    return None


def is_valid_url(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parts = urlparse(value.strip())
    except ValueError:
        return False
    return parts.scheme in ("http", "https") and bool(parts.netloc)


def news_id_for(origen: str, url: str) -> str:
    """Deterministic news id: ``<origen>-<sha256(url)[:12]>``."""
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    return f"{origen}-{digest}"


def validate_news(rows: list[dict]) -> ValidationResult:
    result = ValidationResult()
    seen_urls: set[str] = set()
    kept_tokens: list[set[str]] = []
    for i, row in enumerate(rows):
        titulo = (row.get("titulo") or "").strip()
        url = (row.get("url") or "").strip()
        if not titulo or not is_valid_url(url):
            result.dropped += 1
            result.errors.append({"row": i, "reason": "missing titulo or invalid url"})
            continue
        if url in seen_urls:
            result.dropped += 1
            result.errors.append({"row": i, "reason": "duplicate url", "url": url})
            continue
        tokens = title_tokens(titulo)
        if tokens and any(jaccard(tokens, prev) >= TITLE_DEDUP_JACCARD for prev in kept_tokens):
            result.dropped += 1
            result.errors.append({"row": i, "reason": "near-duplicate title", "titulo": titulo})
            continue
        seen_urls.add(url)
        kept_tokens.append(tokens)
        clean = dict(row)
        clean["titulo"] = titulo
        clean["url"] = url
        clean["id_noticia"] = row.get("id_noticia") or news_id_for(
            str(row.get("origen") or "na"), url
        )
        for field_name in ("fecha_publicacion", "fecha_deteccion", "fecha_extraccion"):
            parsed = parse_datetime(row.get(field_name))
            if row.get(field_name) not in (None, "") and parsed is None:
                result.errors.append(
                    {"row": i, "reason": f"invalid {field_name}", "value": str(row.get(field_name))}
                )
            clean[field_name] = parsed
        if not clean.get("medio"):
            clean["medio"] = "desconocido"
            result.errors.append({"row": i, "reason": "missing medio, defaulted"})
        result.valid.append(clean)
    return result


def validate_indicators(rows: list[dict]) -> ValidationResult:
    result = ValidationResult()
    seen: set[tuple] = set()
    for i, row in enumerate(rows):
        pais = (row.get("pais_iso3") or "").strip().upper()
        indicador = (row.get("indicador_id") or "").strip()
        try:
            anio = int(row["anio"]) if row.get("anio") not in (None, "") else None
        except (TypeError, ValueError):
            anio = None
        if not pais or not indicador or anio is None:
            result.dropped += 1
            result.errors.append({"row": i, "reason": "missing pais_iso3/indicador_id/anio"})
            continue
        key = (pais, indicador, anio)
        if key in seen:
            result.dropped += 1
            result.errors.append({"row": i, "reason": "duplicate observation"})
            continue
        seen.add(key)
        clean = dict(row)
        clean["pais_iso3"] = pais
        clean["indicador_id"] = indicador
        clean["anio"] = anio
        valor = row.get("valor")
        if valor in ("", "null", "None"):
            valor = None
        if valor is not None:
            try:
                valor = float(valor)
            except (TypeError, ValueError):
                result.errors.append({"row": i, "reason": "invalid valor, nulled"})
                valor = None
        clean["valor"] = valor  # nulls kept explicit
        clean["fecha_extraccion"] = parse_datetime(row.get("fecha_extraccion"))
        result.valid.append(clean)
    return result


def validate_events(rows: list[dict]) -> ValidationResult:
    result = ValidationResult()
    seen: set[str] = set()
    for i, row in enumerate(rows):
        event_id = (row.get("id") or "").strip()
        if not event_id:
            result.dropped += 1
            result.errors.append({"row": i, "reason": "missing event id"})
            continue
        if event_id in seen:
            result.dropped += 1
            result.errors.append({"row": i, "reason": "duplicate event id"})
            continue
        seen.add(event_id)
        clean = dict(row)
        clean["id"] = event_id
        clean["time"] = parse_datetime(row.get("time"))
        clean["updated"] = parse_datetime(row.get("updated"))
        for numeric in ("magnitude", "longitude", "latitude", "depth"):
            value = row.get(numeric)
            if value in ("", None):
                clean[numeric] = None
            else:
                try:
                    clean[numeric] = float(value)
                except (TypeError, ValueError):
                    result.errors.append({"row": i, "reason": f"invalid {numeric}, nulled"})
                    clean[numeric] = None
        result.valid.append(clean)
    return result


def validate_fichas(rows: list[dict]) -> ValidationResult:
    result = ValidationResult()
    seen_ids: set[str] = set()
    for i, row in enumerate(rows):
        id_caso = (row.get("id_caso") or "").strip()
        modalidad = (row.get("modalidad") or "").strip().lower()
        if not id_caso or modalidad not in ("tvn", "banca"):
            result.dropped += 1
            result.errors.append({"row": i, "reason": "missing id_caso or invalid modalidad"})
            continue
        if id_caso in seen_ids:
            result.dropped += 1
            result.errors.append({"row": i, "reason": "duplicate id_caso", "id_caso": id_caso})
            continue
        seen_ids.add(id_caso)
        clean = dict(row)
        clean["id_caso"] = id_caso
        clean["modalidad"] = modalidad
        clean["ids_fuente"] = list(row.get("ids_fuente") or [])
        clean["afirmaciones"] = list(row.get("afirmaciones") or [])
        clean["citas"] = list(row.get("citas") or [])
        try:
            clean["puntaje"] = float(row.get("puntaje", 0.0))
        except (TypeError, ValueError):
            clean["puntaje"] = 0.0
            result.errors.append({"row": i, "reason": "invalid puntaje, defaulted to 0.0"})
        clean["componentes"] = dict(row.get("componentes") or {})
        clean["estado_evidencia"] = str(row.get("estado_evidencia") or "insuficiente")
        clean["borrador"] = str(row.get("borrador") or "")
        clean["estado_revision"] = str(row.get("estado_revision") or "nuevo")
        result.valid.append(clean)
    return result

