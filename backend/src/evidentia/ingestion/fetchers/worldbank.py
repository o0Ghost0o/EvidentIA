"""World Bank Indicators API v2 fetcher (family B).

Grid: 6 countries (PAN, CRI, COL, DOM, MEX, GTM) x 6 indicators x 2010-2024.
Missing values are kept explicit (None) per the challenge contract.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx

from evidentia.ingestion.fetchers._http import get_with_retry

logger = logging.getLogger(__name__)

WB_BASE_URL = "https://api.worldbank.org/v2"

COUNTRIES = ["PAN", "CRI", "COL", "DOM", "MEX", "GTM"]
YEARS = "2010:2024"

# indicator_id -> human unit label (the API returns unit="").
INDICATORS = {
    "NY.GDP.MKTP.KD.ZG": "% anual",  # GDP growth
    "FP.CPI.TOTL.ZG": "% anual",  # inflation
    "SL.UEM.TOTL.ZS": "%",  # unemployment
    "SP.POP.TOTL": "personas",  # population
    "IT.NET.USER.ZS": "% población",  # internet use
    "NE.EXP.GNFS.ZS": "% del PIB",  # exports/GDP
}

HTTP_TIMEOUT_SECONDS = 60.0


def fetch_worldbank_indicators(
    countries: list[str] | None = None,
    indicators: dict[str, str] | None = None,
    years: str = YEARS,
) -> list[dict]:
    """Fetch indicator observations normalised to ``indicadores.csv``."""
    countries = countries or COUNTRIES
    indicators = indicators or INDICATORS
    rows: list[dict] = []
    now = datetime.now(timezone.utc)
    with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS) as client:
        for indicator_id, unidad in indicators.items():
            url = f"{WB_BASE_URL}/country/{';'.join(countries)}/indicator/{indicator_id}"
            resp = get_with_retry(
                client, url,
                params={"date": years, "format": "json", "per_page": 500},
                what=f"World Bank {indicator_id}",
            )
            payload = resp.json()
            obs = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
            for ob in obs or []:
                try:
                    anio = int(ob.get("date"))
                except (TypeError, ValueError):
                    continue
                rows.append(
                    {
                        "pais_iso3": ob.get("countryiso3code") or "",
                        "indicador_id": indicator_id,
                        "anio": anio,
                        "valor": ob.get("value"),  # None kept explicit
                        "unidad": unidad,
                        "fuente_url": url,
                        "fecha_extraccion": now,
                        "licencia": "CC BY 4.0",
                    }
                )
            logger.info("World Bank %s → %d obs", indicator_id, len(obs or []))
    return rows
