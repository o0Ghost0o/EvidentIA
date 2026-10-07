"""USGS Earthquake Catalog fetcher (family C, GeoJSON).

Regional box lat 5–12 / lon -86–-76, full year 2024, magnitude >= 3.
The box is NOT Panama's territory — locations are kept verbatim and the source
is used for seismic facts only.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from evidentia.ingestion.fetchers._http import get_with_retry

logger = logging.getLogger(__name__)

USGS_BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

HTTP_TIMEOUT_SECONDS = 60.0


def _epoch_ms_to_dt(value: int | float | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(float(value) / 1000, tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return None


def fetch_usgs_events(
    starttime: str = "2024-01-01",
    endtime: str = "2024-12-31",
    min_latitude: float = 5.0,
    max_latitude: float = 12.0,
    min_longitude: float = -86.0,
    max_longitude: float = -76.0,
    min_magnitude: float = 3.0,
    limit: int = 2000,
) -> list[dict]:
    """Fetch seismic events normalised to the ``eventos.geojson`` contract."""
    params = {
        "format": "geojson",
        "starttime": starttime,
        "endtime": endtime,
        "minlatitude": min_latitude,
        "maxlatitude": max_latitude,
        "minlongitude": min_longitude,
        "maxlongitude": max_longitude,
        "minmagnitude": min_magnitude,
        "limit": limit,
        "orderby": "time",
    }
    with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS) as client:
        resp = get_with_retry(client, USGS_BASE_URL, params=params, what="USGS")
        payload = resp.json()
    features = payload.get("features", []) if isinstance(payload, dict) else []
    rows: list[dict] = []
    for feat in features:
        props = feat.get("properties", {}) or {}
        geom = feat.get("geometry", {}) or {}
        coords = geom.get("coordinates", []) or []
        rows.append(
            {
                "id": feat.get("id") or "",
                "magnitude": props.get("mag"),
                "time": _epoch_ms_to_dt(props.get("time")),
                "updated": _epoch_ms_to_dt(props.get("updated")),
                "longitude": coords[0] if len(coords) > 0 else None,
                "latitude": coords[1] if len(coords) > 1 else None,
                "depth": coords[2] if len(coords) > 2 else None,
                "place": props.get("place"),
                "status": props.get("status"),
                "url": props.get("url"),
            }
        )
    logger.info("USGS → %d events", len(rows))
    return rows
