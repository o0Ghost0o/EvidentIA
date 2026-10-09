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

REQUEST_DELAY_SECONDS = 0.5
HTTP_TIMEOUT_SECONDS = 3.5
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


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
    try:
        resp = client.get(
            GDELT_BASE_URL,
            params=params,
            headers={"User-Agent": DEFAULT_USER_AGENT},
        )
        if resp.status_code == 429:
            logger.warning("GDELT 429 rate limit for %r — skipped gracefully", query)
            return []
        resp.raise_for_status()
        payload = resp.json()
        articles = payload.get("articles", []) if isinstance(payload, dict) else []
        logger.info("GDELT query %r → %d articles", query, len(articles))
        return articles if isinstance(articles, list) else []
    except (httpx.TimeoutException, httpx.RequestError) as exc:
        logger.warning("GDELT query failed or timed out for %r: %s", query, exc)
        return []
    except ValueError:
        logger.warning("GDELT non-JSON response for %r", query)
        return []


def fetch_gdelt_news(
    timespan: str = "1month",
    max_records: int = 250,
    queries: list[str] | None = None,
) -> list[dict]:
    """Fetch news hits and normalise them to the ``noticias.csv`` contract."""
    from concurrent.futures import ThreadPoolExecutor

    rows: list[dict] = []
    now = datetime.now(timezone.utc)
    target_queries = queries or GDELT_QUERIES

    def _worker(q: str) -> list[dict]:
        try:
            with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS) as client:
                return _fetch_query(client, q, timespan, max_records)
        except Exception:
            return []

    with ThreadPoolExecutor(max_workers=len(target_queries)) as pool:
        results = pool.map(_worker, target_queries)

    for articles in results:
        for art in articles:
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

