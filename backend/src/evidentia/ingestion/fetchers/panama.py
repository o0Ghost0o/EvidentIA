"""Additional Panamanian public-press RSS feeds (news family A).

Added for T-04: broaden the corpus beyond TVN with independent national outlets
so corroboration and medio diversity are possible. Only titles/links/metadata
are consumed — no article bodies, no republication. Each feed's source, URL and
licence are recorded in the data catalogue (notion/03).
"""

from __future__ import annotations

import logging

from evidentia.ingestion.fetchers.rss import rss_rows

logger = logging.getLogger(__name__)

# (medio, origen, url) for each public Panamanian feed. Verified 2026-10-07.
PANAMA_FEEDS: list[dict[str, str]] = [
    {
        "medio": "La Prensa",
        "origen": "laprensa",
        "url": "https://www.prensa.com/arc/outboundfeeds/rss/?outputType=xml",
    },
    {
        "medio": "Crítica",
        "origen": "critica",
        "url": "https://critica.com.pa/rss.xml",
    },
]


def fetch_panama_news(
    feeds: list[dict[str, str]] | None = None,
    days: int = 90,
    max_records: int = 150,
) -> list[dict]:
    """Fetch every configured Panamanian feed, normalised to the news contract.

    A single feed failing is logged and skipped so one outlet's downtime never
    sinks the whole family.
    """
    rows: list[dict] = []
    for feed in feeds or PANAMA_FEEDS:
        try:
            rows.extend(
                rss_rows(
                    feed["url"],
                    medio=feed["medio"],
                    origen=feed["origen"],
                    days=days,
                    max_records=max_records,
                )
            )
        except Exception as exc:  # noqa: BLE001 — isolate per-feed failures
            logger.warning("Panama feed %s failed: %s", feed.get("origen"), exc)
    return rows
