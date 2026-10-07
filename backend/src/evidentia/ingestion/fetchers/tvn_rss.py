"""TVN public RSS fetcher (news family A, sponsor metadata).

The feed URL is operator-configured (``TVN_RSS_URL``) because feed paths change;
when unset the fetcher is skipped gracefully and the quality report records it.
Only titles/links/metadata are consumed — no article bodies, no republication.
The window defaults to 90 days (challenge §6A: widen coverage and record it).
"""

from __future__ import annotations

from evidentia.ingestion.fetchers.rss import rss_rows


def fetch_tvn_news(feed_url: str = "", max_records: int = 150, days: int = 90) -> list[dict]:
    """Fetch TVN headlines normalised to the ``noticias.csv`` contract."""
    return rss_rows(feed_url, medio="TVN", origen="tvn", days=days, max_records=max_records)
