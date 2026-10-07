"""GDELT DOC 2.0 fetcher (news family A).

API notes (verified 2026-10-06): ``mode=artlist&format=json`` returns
``{"articles": [{url, url_mobile, title, seendate, socialimage, domain,
language, sourcecountry}]}``. Hard rate limit of ~1 request / 5 seconds with
HTTP 429 beyond it, so queries are throttled and retried once after 30 s.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

GDELT_BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

# Queries covering the challenge themes; split by query because the API caps
# results per call (250) — dedup by URL happens in validators.
GDELT_QUERIES = [
    "Panama",
    "Canal de Panamá",
    "Panamá economía",
    "Panamá turismo",
]

LANGUAGE_MAP = {"english": "en", "spanish": "es"}

REQUEST_DELAY_SECONDS = 8.0
RETRY_AFTER_429_SECONDS = (30.0, 90.0, 240.0)
HTTP_TIMEOUT_SECONDS = 45.0


def _parse_seendate(value: str | None) -> datetime | None:
    """Parse GDELT seendate (``YYYYMMDDTHHMMSSZ``) to aware UTC datetime."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _fetch_query(
    client: httpx.Client, query: str, timespan: str, max_records: int
) -> list[dict]:
    params = {
        "query": query,
        "mode": "artlist",
        "format": "json",
        "maxrecords": max_records,
        "timespan": timespan,
        "sort": "datedesc",
    }
    for attempt, wait in enumerate((0.0, *RETRY_AFTER_429_SECONDS)):
        if wait:
            logger.warning("GDELT 429 for %r — retrying in %ss", query, wait)
            time.sleep(wait)
        try:
            resp = client.get(GDELT_BASE_URL, params=params)
        except httpx.TimeoutException:
            if attempt < len(RETRY_AFTER_429_SECONDS):
                logger.warning("GDELT timeout for %r — backing off", query)
                continue  # next attempt sleeps via its wait slot
            raise
        if resp.status_code == 429 and attempt < len(RETRY_AFTER_429_SECONDS):
            continue
        resp.raise_for_status()
        try:
            payload = resp.json()
        except ValueError:
            logger.warning("GDELT non-JSON response for %r", query)
            return []
        articles = payload.get("articles", []) if isinstance(payload, dict) else []
        logger.info("GDELT query %r → %d articles", query, len(articles))
        return articles if isinstance(articles, list) else []
    return []


def fetch_gdelt_news(
    timespan: str = "1month",
    max_records: int = 250,
    queries: list[str] | None = None,
) -> list[dict]:
    """Fetch news hits and normalise them to the ``noticias.csv`` contract."""
    rows: list[dict] = []
    now = datetime.now(timezone.utc)
    with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS) as client:
        for i, query in enumerate(queries or GDELT_QUERIES):
            if i > 0:
                time.sleep(REQUEST_DELAY_SECONDS)
            for art in _fetch_query(client, query, timespan, max_records):
                published = _parse_seendate(art.get("seendate"))
                rows.append(
                    {
                        "titulo": (art.get("title") or "").strip(),
                        "url": (art.get("url") or "").strip(),
                        "medio": (art.get("domain") or "").strip(),
                        "idioma": LANGUAGE_MAP.get((art.get("language") or "").lower(), "otro"),
                        "fecha_publicacion": published,
                        "fecha_deteccion": published,
                        "fecha_extraccion": now,
                        "tema": None,  # classified in Fase 3
                        "origen": "gdelt",
                        "alcance_texto": "titular",
                    }
                )
    return rows
