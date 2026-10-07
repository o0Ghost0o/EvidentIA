#!/usr/bin/env python3
"""Build the frozen offline snapshot in ``data/seed/`` from live public APIs.

Run from the repository root (backend env active)::

    uv --project backend run python scripts/fetch_seed_data.py

The snapshot keeps the demo and T10 runnable without internet. Contents are
trimmed for size but otherwise real API responses, validated through the same
validators as live ingestion.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend" / "src"))

from evidentia.ingestion import fetchers, manifest as manifest_mod, validators  # noqa: E402
from evidentia.ingestion.pipeline import INDICATOR_FIELDS, NEWS_FIELDS  # noqa: E402

SEED_NEWS_MAX = 60
SEED_EVENTS_MAX = 100


def main() -> None:
    seed_dir = ROOT / "data" / "seed"
    seed_dir.mkdir(parents=True, exist_ok=True)

    failures: list[str] = []
    try:
        print("Fetching GDELT…")
        news_raw = fetchers.fetch_gdelt_news()
        print(f"  {len(news_raw)} hits")
    except Exception as exc:
        failures.append(f"gdelt: {exc}")
        news_raw = []
        print(f"  FAILED: {exc}")

    try:
        print("Fetching World Bank…")
        ind_raw = fetchers.fetch_worldbank_indicators()
        print(f"  {len(ind_raw)} obs")
    except Exception as exc:
        failures.append(f"worldbank: {exc}")
        ind_raw = []
        print(f"  FAILED: {exc}")

    try:
        print("Fetching USGS…")
        evt_raw = fetchers.fetch_usgs_events()
        print(f"  {len(evt_raw)} events")
    except Exception as exc:
        failures.append(f"usgs: {exc}")
        evt_raw = []
        print(f"  FAILED: {exc}")

    if failures:
        print(f"WARNING: partial snapshot ({len(failures)} families failed)")

    news = validators.validate_news(news_raw).valid[:SEED_NEWS_MAX]
    indicators = validators.validate_indicators(ind_raw).valid
    events = validators.validate_events(evt_raw).valid[:SEED_EVENTS_MAX]

    def iso(v):
        from datetime import datetime

        if isinstance(v, datetime):
            from datetime import timezone

            return v.astimezone(timezone.utc).isoformat()
        return "" if v is None else str(v)

    with (seed_dir / "noticias.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=NEWS_FIELDS, extrasaction="ignore")
        w.writeheader()
        for row in news:
            w.writerow({k: iso(row.get(k)) for k in NEWS_FIELDS})

    with (seed_dir / "indicadores.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=INDICATOR_FIELDS, extrasaction="ignore")
        w.writeheader()
        for row in indicators:
            w.writerow({k: iso(row.get(k)) for k in INDICATOR_FIELDS})

    features = []
    for row in events:
        lon, lat = row.get("longitude"), row.get("latitude")
        features.append(
            {
                "type": "Feature",
                "id": row.get("id"),
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat] if lon is not None and lat is not None else [],
                },
                "properties": {
                    "mag": row.get("magnitude"),
                    "time": iso(row.get("time")),
                    "updated": iso(row.get("updated")),
                    "depth": row.get("depth"),
                    "place": row.get("place"),
                    "status": row.get("status"),
                    "url": row.get("url"),
                },
            }
        )
    (seed_dir / "eventos.geojson").write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False),
        encoding="utf-8",
    )

    counts = {
        "noticias.csv": len(news),
        "indicadores.csv": len(indicators),
        "eventos.geojson": len(events),
    }
    queries = {
        "gdelt": {"queries": fetchers.gdelt.GDELT_QUERIES},
        "worldbank": {"countries": fetchers.worldbank.COUNTRIES},
        "usgs": {"box": "lat 5–12, lon -86–-76, 2024, mag>=3"},
    }
    seed_manifest = manifest_mod.build_manifest(seed_dir, counts, queries, source="live-seed-build")
    manifest_mod.write_manifest(seed_dir, seed_manifest)
    print(f"Seed written to {seed_dir}: {counts}")


if __name__ == "__main__":
    main()
