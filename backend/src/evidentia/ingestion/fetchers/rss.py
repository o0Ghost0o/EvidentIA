"""Shared RSS normalisation for news-family feeds (TVN + Panamanian press).

Every feed is reduced to the ``noticias.csv`` contract: only titles, links and
metadata are consumed — never article bodies, no republication. Entries are
filtered to a rolling window (default 90 days); entries without a parseable date
are kept so a missing ``pubDate`` never silently drops a headline.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


def rss_rows(
    feed_url: str,
    *,
    medio: str,
    origen: str,
    days: int = 90,
    max_records: int = 150,
) -> list[dict]:
    """Fetch one RSS feed, window-filter by publish date, normalise rows.

    Returns rows newest-first as they appear in the feed. Entries older than
    ``days`` are dropped; entries with no parseable date are retained.
    """
    if not feed_url:
        logger.warning("%s feed url unset — skipped", origen)
        return []
    import feedparser  # lazy: keeps import surface small

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }
    parsed = feedparser.parse(feed_url, agent=headers["User-Agent"], request_headers=headers)
    if getattr(parsed, "bozo", False):
        logger.warning("%s feed parse issue: %s", origen, getattr(parsed, "bozo_exception", "?"))

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    rows: list[dict] = []
    seen_total = 0
    oldest_kept: datetime | None = None
    newest_kept: datetime | None = None
    for entry in (parsed.entries or []):
        seen_total += 1
        published = None
        if getattr(entry, "published_parsed", None):
            try:
                published = datetime.fromtimestamp(
                    time.mktime(entry.published_parsed), tz=timezone.utc
                )
            except (TypeError, ValueError, OverflowError):
                published = None
        # Window filter: drop dated entries older than the cutoff; keep undated.
        if published is not None and published < cutoff:
            continue
        if published is not None:
            oldest_kept = published if oldest_kept is None else min(oldest_kept, published)
            newest_kept = published if newest_kept is None else max(newest_kept, published)
        summary = (getattr(entry, "summary", "") or "").strip()
        rows.append(
            {
                "titulo": (getattr(entry, "title", "") or "").strip(),
                "url": (getattr(entry, "link", "") or "").strip(),
                "medio": medio,
                "idioma": "es",
                "fecha_publicacion": published,
                "fecha_deteccion": published,
                "fecha_extraccion": now,
                "tema": None,
                "origen": origen,
                "alcance_texto": "extracto" if summary else "titular",
            }
        )
        if len(rows) >= max_records:
            break
    logger.info(
        "%s RSS → %d entries kept of %d seen (window %dd, %s…%s)",
        origen,
        len(rows),
        seen_total,
        days,
        oldest_kept.date().isoformat() if oldest_kept else "?",
        newest_kept.date().isoformat() if newest_kept else "?",
    )
    return rows
