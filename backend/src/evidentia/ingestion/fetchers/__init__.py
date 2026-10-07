"""Public-source fetchers (GDELT, World Bank, USGS, TVN RSS)."""

from evidentia.ingestion.fetchers.gdelt import fetch_gdelt_news
from evidentia.ingestion.fetchers.tvn_rss import fetch_tvn_news
from evidentia.ingestion.fetchers.usgs import fetch_usgs_events
from evidentia.ingestion.fetchers.worldbank import fetch_worldbank_indicators

__all__ = [
    "fetch_gdelt_news",
    "fetch_tvn_news",
    "fetch_usgs_events",
    "fetch_worldbank_indicators",
]
