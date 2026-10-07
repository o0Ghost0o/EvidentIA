#!/usr/bin/env python3
"""Build the frozen offline snapshot in ``data/seed/`` from live public APIs.

Run from the repository root (backend env active)::

    uv --project backend run python scripts/fetch_seed_data.py

The snapshot keeps the demo and T10 runnable without internet. Contents are
trimmed for size but otherwise real API responses, validated through the same
validators as live ingestion.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend" / "src"))

from evidentia.ingestion import fetchers, manifest as manifest_mod, validators  # noqa: E402
from evidentia.ingestion.pipeline import INDICATOR_FIELDS, NEWS_FIELDS  # noqa: E402

SEED_NEWS_MAX = 150
SEED_EVENTS_MAX = 100


def _round_robin(*sources: list[dict]) -> list[dict]:
    """Interleave per-source lists so a later cap keeps every outlet present."""
    from itertools import zip_longest

    merged: list[dict] = []
    for tier in zip_longest(*sources):
        merged.extend(row for row in tier if row is not None)
    return merged


def _load_existing_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as fh:
        return [dict(r) for r in csv.DictReader(fh) if r.get("titulo") or r.get("pais_iso3")]


def _load_existing_geojson(path: Path) -> list[dict]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for feat in payload.get("features", []):
        props = feat.get("properties", {}) or {}
        coords = (feat.get("geometry", {}) or {}).get("coordinates", []) or []
        rows.append({
            "id": feat.get("id"), "magnitude": props.get("mag"),
            "time": props.get("time") or None, "updated": props.get("updated") or None,
            "longitude": coords[0] if len(coords) > 0 else None,
            "latitude": coords[1] if len(coords) > 1 else None,
            "depth": props.get("depth"), "place": props.get("place"),
            "status": props.get("status"), "url": props.get("url"),
        })
    return rows


def main(only: set[str] | None = None) -> None:
    seed_dir = ROOT / "data" / "seed"
    seed_dir.mkdir(parents=True, exist_ok=True)
    only = only or {"tvn", "panama", "worldbank", "usgs"}
    # Merge mode: existing seed rows are always preloaded; freshly fetched rows
    # go first so validators (dedup keeps first) prefer them. News sources are
    # round-robin interleaved so the seed cap keeps every outlet represented.
    # GDELT is not fetched by default (persistent HTTP 429); its recipe is kept
    # in the manifest as metadata, never its content.
    want_news = bool({"gdelt", "tvn", "panama"} & only)
    existing_news = _load_existing_csv(seed_dir / "noticias.csv")
    news_raw: list[dict] = existing_news if not want_news else []
    ind_raw: list[dict] = _load_existing_csv(seed_dir / "indicadores.csv")
    evt_raw: list[dict] = _load_existing_geojson(seed_dir / "eventos.geojson")

    failures: list[str] = []
    if want_news:  # news family = TVN RSS + Panamanian press (+ optional GDELT)
        tvn_rows: list[dict] = []
        panama_by_source: dict[str, list[dict]] = {}
        gdelt_rows: list[dict] = []
        if "tvn" not in only:
            print("Skipping TVN RSS (not in --only).")
        else:
            try:
                print("Fetching TVN RSS (90-day window)…")
                tvn_rows = fetchers.fetch_tvn_news(
                    os.environ.get("TVN_RSS_URL", "https://www.tvn-2.com/rss")
                )
                print(f"  {len(tvn_rows)} entries")
            except Exception as exc:
                failures.append(f"tvn: {exc}")
                print(f"  FAILED: {exc}")
        if "panama" not in only:
            print("Skipping Panamanian feeds (not in --only).")
        else:
            for feed in fetchers.PANAMA_FEEDS:
                try:
                    print(f"Fetching {feed['medio']} RSS (90-day window)…")
                    rows = fetchers.fetch_panama_news([feed])
                    panama_by_source[feed["origen"]] = rows
                    print(f"  {len(rows)} entries")
                except Exception as exc:
                    failures.append(f"{feed['origen']}: {exc}")
                    print(f"  FAILED: {exc}")
        if "gdelt" in only:  # opt-in only; off by default due to HTTP 429
            try:
                print("Fetching GDELT…")
                gdelt_rows = fetchers.fetch_gdelt_news()
                print(f"  {len(gdelt_rows)} hits")
            except Exception as exc:
                failures.append(f"gdelt: {exc}")
                print(f"  FAILED: {exc}")
        # Interleave sources so the seed cap keeps every outlet represented.
        combined = _round_robin(tvn_rows, *panama_by_source.values(), gdelt_rows)
        news_raw = (combined + existing_news) if combined else existing_news
        if not combined:
            print(f"  (kept {len(news_raw)} existing)")

    if "worldbank" in only:
        try:
            print("Fetching World Bank…")
            fresh = fetchers.fetch_worldbank_indicators()
            ind_raw = fresh + ind_raw
            print(f"  {len(fresh)} obs")
        except Exception as exc:
            failures.append(f"worldbank: {exc}")
            print(f"  FAILED: {exc} (kept {len(ind_raw)} existing)")

    if "usgs" in only:
        try:
            print("Fetching USGS…")
            fresh = fetchers.fetch_usgs_events()
            evt_raw = fresh + evt_raw
            print(f"  {len(fresh)} events")
        except Exception as exc:
            failures.append(f"usgs: {exc}")
            print(f"  FAILED: {exc} (kept {len(evt_raw)} existing)")

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
    if (seed_dir / "fichas.jsonl").exists():
        counts["fichas.jsonl"] = sum(
            1 for line in (seed_dir / "fichas.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()
        )
    queries = {
        "tvn": {"url": "https://www.tvn-2.com/rss", "window_days": 90},
        "panama": {
            "feeds": [
                {"medio": f["medio"], "url": f["url"]} for f in fetchers.PANAMA_FEEDS
            ],
            "window_days": 90,
        },
        "gdelt": {
            "queries": fetchers.gdelt.GDELT_QUERIES,
            "status": "no utilizado — HTTP 429 persistente; receta conservada sin contenido",
        },
        "worldbank": {"countries": fetchers.worldbank.COUNTRIES},
        "usgs": {"box": "lat 5–12, lon -86–-76, 2024, mag>=3"},
    }
    seed_manifest = manifest_mod.build_manifest(seed_dir, counts, queries, source="live-seed-build")
    manifest_mod.write_manifest(seed_dir, seed_manifest)
    print(f"Seed written to {seed_dir}: {counts}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--only", nargs="*", choices=["gdelt", "tvn", "panama", "worldbank", "usgs"]
    )
    args = parser.parse_args()
    main(set(args.only) if args.only else None)
