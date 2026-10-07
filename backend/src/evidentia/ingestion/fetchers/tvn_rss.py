"""TVN public RSS fetcher (news family A, sponsor metadata).

The feed URL is operator-configured (``TVN_RSS_URL``) because feed paths change;
when unset the fetcher is skipped gracefully and the quality report records it.
Only titles/links/metadata are consumed — no article bodies, no republication.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def fetch_tvn_news(feed_url: str = "", max_records: int = 100) -> list[dict]:
    """Fetch TVN headlines normalised to the ``noticias.csv`` contract."""
    if not feed_url:
        logger.warning("TVN_RSS_URL unset — TVN fetcher skipped")
        return []
    import feedparser  # lazy: keeps import surface small

    parsed = feedparser.parse(feed_url)
    if getattr(parsed, "bozo", False):
        logger.warning("TVN feed parse issue: %s", getattr(parsed, "bozo_exception", "?"))
    rows: list[dict] = []
    now = datetime.now(timezone.utc)
    for entry in (parsed.entries or [])[:max_records]:
        published = None
        if getattr(entry, "published_parsed", None):
            try:
                published = datetime.fromtimestamp(
                    time.mktime(entry.published_parsed), tz=timezone.utc
                )
            except (TypeError, ValueError, OverflowError):
                published = None
        summary = (getattr(entry, "summary", "") or "").strip()
        rows.append(
            {
                "titulo": (getattr(entry, "title", "") or "").strip(),
                "url": (getattr(entry, "link", "") or "").strip(),
                "medio": "TVN",
                "idioma": "es",
                "fecha_publicacion": published,
                "fecha_deteccion": published,
                "fecha_extraccion": now,
                "tema": None,
                "origen": "tvn",
                "alcance_texto": "extracto" if summary else "titular",
            }
        )
    logger.info("TVN RSS → %d entries", len(rows))
    return rows
