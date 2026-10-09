"""Ingestion pipeline: fetch → validate → persist files → upsert DB → manifest.

Sources:
  - live: GDELT + TVN RSS (news), World Bank (indicators), USGS (events).
  - seed: frozen snapshot copied from ``seed_dir`` (offline demo / T10).

The pipeline is resilient by design: a failing family is recorded in the
quality report without aborting the others, and a down database degrades to
files-only mode with a warning.
"""

from __future__ import annotations

import csv
import json
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evidentia.ingestion import manifest as manifest_mod
from evidentia.ingestion import validators

logger = logging.getLogger(__name__)

NEWS_FIELDS = [
    "id_noticia", "titulo", "url", "medio", "idioma",
    "fecha_publicacion", "fecha_deteccion", "fecha_extraccion",
    "tema", "origen", "alcance_texto",
]
INDICATOR_FIELDS = [
    "pais_iso3", "indicador_id", "anio", "valor", "unidad",
    "fuente_url", "fecha_extraccion", "licencia",
]


def _iso(value: Any) -> str:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    return "" if value is None else str(value)


def _write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _iso(row.get(k)) for k in fields})


def _write_geojson(path: Path, rows: list[dict]) -> None:
    features = []
    for row in rows:
        lon, lat, depth = row.get("longitude"), row.get("latitude"), row.get("depth")
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
                    "time": _iso(row.get("time")),
                    "updated": _iso(row.get("updated")),
                    "depth": depth,
                    "place": row.get("place"),
                    "status": row.get("status"),
                    "url": row.get("url"),
                },
            }
        )
    path.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False),
        encoding="utf-8",
    )


def _read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _read_geojson(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for feat in payload.get("features", []):
        props = feat.get("properties", {}) or {}
        coords = (feat.get("geometry", {}) or {}).get("coordinates", []) or []
        rows.append(
            {
                "id": feat.get("id"),
                "magnitude": props.get("mag"),
                "time": props.get("time") or None,
                "updated": props.get("updated") or None,
                "longitude": coords[0] if len(coords) > 0 else None,
                "latitude": coords[1] if len(coords) > 1 else None,
                "depth": props.get("depth"),
                "place": props.get("place"),
                "status": props.get("status"),
                "url": props.get("url"),
            }
        )
    return rows


def _upsert_db(news: list[dict], indicators: list[dict], events: list[dict]) -> dict[str, int]:
    """Upsert validated rows; returns per-table counts."""
    from sqlmodel import Session, select

    from evidentia import models
    from evidentia.db import get_engine

    counts = {"news_articles": 0, "indicators": 0, "geo_events": 0}
    with Session(get_engine()) as session:
        for row in news:
            obj = session.exec(
                select(models.NewsArticle).where(
                    models.NewsArticle.id_noticia == row["id_noticia"]
                )
            ).first()
            if obj is None:
                obj = models.NewsArticle()
                session.add(obj)
            for key in NEWS_FIELDS:
                setattr(obj, key, row.get(key) or None)
            # restore non-nullable values possibly blanked above
            obj.titulo = row["titulo"]
            obj.url = row["url"]
            obj.idioma = row.get("idioma") or "es"
            obj.origen = row.get("origen") or "gdelt"
            obj.alcance_texto = row.get("alcance_texto") or "titular"
            obj.fecha_extraccion = row.get("fecha_extraccion") or datetime.now(timezone.utc)
            counts["news_articles"] += 1
        for row in indicators:
            obj = session.exec(
                select(models.Indicator).where(
                    models.Indicator.pais_iso3 == row["pais_iso3"],
                    models.Indicator.indicador_id == row["indicador_id"],
                    models.Indicator.anio == row["anio"],
                )
            ).first()
            if obj is None:
                obj = models.Indicator()
                session.add(obj)
            for key in INDICATOR_FIELDS:
                setattr(obj, key, row.get(key) or None)
            obj.pais_iso3, obj.indicador_id, obj.anio = (
                row["pais_iso3"], row["indicador_id"], row["anio"],
            )
            obj.licencia = row.get("licencia") or "CC BY 4.0"
            obj.fecha_extraccion = row.get("fecha_extraccion") or datetime.now(timezone.utc)
            counts["indicators"] += 1
        for row in events:
            obj = session.exec(
                select(models.GeoEvent).where(models.GeoEvent.event_id == row["id"])
            ).first()
            if obj is None:
                obj = models.GeoEvent(event_id=row["id"])
                session.add(obj)
            obj.magnitude = row.get("magnitude")
            obj.time = row.get("time")
            obj.updated = row.get("updated")
            obj.longitude = row.get("longitude")
            obj.latitude = row.get("latitude")
            obj.depth = row.get("depth")
            obj.place = row.get("place")
            obj.status = row.get("status")
            obj.url = row.get("url")
            counts["geo_events"] += 1
        session.commit()
    return counts


def run_ingestion(
    use_seed: bool = False,
    data_dir: Path | None = None,
    seed_dir: Path | None = None,
    tvn_rss_url: str = "",
) -> dict[str, Any]:
    """Run the full ingestion; returns the quality report (also persisted)."""
    from evidentia.config import get_settings, resolve_data_path

    settings = get_settings()
    data_dir = resolve_data_path(data_dir or settings.data_dir)
    seed_dir = resolve_data_path(seed_dir or settings.seed_dir)
    processed = data_dir / "processed"
    processed.mkdir(parents=True, exist_ok=True)

    report: dict[str, Any] = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "source": "seed" if use_seed else "live",
        "families": {},
        "db": None,
        "warnings": [],
    }
    queries: dict[str, object] = {}

    if use_seed:
        from evidentia.config import ensure_seed_files

        ensure_seed_files(seed_dir)
        for name in ("noticias.csv", "indicadores.csv", "eventos.geojson", "fichas.jsonl"):
            src = seed_dir / name
            if not src.exists():
                alt = resolve_data_path(Path("data/seed") / name)
                if alt.exists():
                    src = alt
            if not src.exists():
                alt2 = Path("/app/seed_frozen") / name
                if alt2.exists():
                    src = alt2
            if not src.exists():
                report["warnings"].append(f"seed file missing: {name}")
                continue
            shutil.copy(src, processed / name)
        news_raw = _read_csv(processed / "noticias.csv") if (processed / "noticias.csv").exists() else []
        ind_raw = _read_csv(processed / "indicadores.csv") if (processed / "indicadores.csv").exists() else []
        evt_raw = _read_geojson(processed / "eventos.geojson") if (processed / "eventos.geojson").exists() else []
        queries = {"seed_dir": str(seed_dir)}
    else:
        from concurrent.futures import ThreadPoolExecutor
        from evidentia.ingestion import fetchers

        news_raw: list[dict] = []
        ind_raw: list[dict] = []
        evt_raw: list[dict] = []

        def _get_tvn():
            return fetchers.fetch_tvn_news(tvn_rss_url or settings.tvn_rss_url)

        def _get_panama():
            return fetchers.fetch_panama_news()

        def _get_gdelt():
            return fetchers.fetch_gdelt_news()

        def _get_indicators():
            return fetchers.fetch_worldbank_indicators()

        def _get_events():
            return fetchers.fetch_usgs_events()

        with ThreadPoolExecutor(max_workers=5) as executor:
            fut_tvn = executor.submit(_get_tvn)
            fut_panama = executor.submit(_get_panama)
            fut_gdelt = executor.submit(_get_gdelt)
            fut_ind = executor.submit(_get_indicators)
            fut_evt = executor.submit(_get_events)

            try:
                tvn_rows = fut_tvn.result()
                news_raw.extend(tvn_rows)
                queries["tvn"] = {"hits": len(tvn_rows)}
            except Exception as exc:
                report["warnings"].append(f"tvn failed: {exc}")
                logger.exception("TVN fetch failed")

            try:
                panama_rows = fut_panama.result()
                news_raw.extend(panama_rows)
                queries["panama"] = {
                    "feeds": [f["medio"] for f in fetchers.PANAMA_FEEDS],
                    "hits": len(panama_rows),
                }
            except Exception as exc:
                report["warnings"].append(f"panama failed: {exc}")
                logger.exception("Panama feeds fetch failed")

            try:
                gdelt_rows = fut_gdelt.result()
                news_raw.extend(gdelt_rows)
                queries["gdelt"] = {"queries": fetchers.gdelt.GDELT_QUERIES, "hits": len(gdelt_rows)}
            except Exception as exc:
                report["warnings"].append(f"gdelt failed: {exc}")
                logger.exception("GDELT fetch failed")

            try:
                ind_raw = fut_ind.result()
                queries["worldbank"] = {"rows": len(ind_raw)}
            except Exception as exc:
                ind_raw = []
                report["warnings"].append(f"worldbank failed: {exc}")
                logger.exception("World Bank fetch failed")

            try:
                evt_raw = fut_evt.result()
                queries["usgs"] = {"rows": len(evt_raw)}
            except Exception as exc:
                evt_raw = []
                report["warnings"].append(f"usgs failed: {exc}")
                logger.exception("USGS fetch failed")

        # If all live news sources failed or were unreachable, fallback to seed news
        if not news_raw:
            fallback_seed = seed_dir / "noticias.csv"
            if not fallback_seed.exists():
                fallback_seed = resolve_data_path(Path("data/seed") / "noticias.csv")
            if fallback_seed.exists():
                news_raw = _read_csv(fallback_seed)
                report["warnings"].append("live news returned 0 items; used seed fallback")


    news = validators.validate_news(news_raw)
    indicators = validators.validate_indicators(ind_raw)
    events = validators.validate_events(evt_raw)

    _write_csv(processed / "noticias.csv", news.valid, NEWS_FIELDS)
    _write_csv(processed / "indicadores.csv", indicators.valid, INDICATOR_FIELDS)
    _write_geojson(processed / "eventos.geojson", events.valid)

    for name, res in (("noticias.csv", news), ("indicadores.csv", indicators), ("eventos.geojson", events)):
        report["families"][name] = {
            "raw": len(news_raw) if name == "noticias.csv" else (
                len(ind_raw) if name == "indicadores.csv" else len(evt_raw)),
            "valid": len(res.valid),
            "dropped": res.dropped,
            "error_sample": res.errors[:10],
            "error_count": len(res.errors),
        }

    if (processed / "fichas.jsonl").exists():
        fichas_raw = [
            json.loads(line)
            for line in (processed / "fichas.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        fichas_res = validators.validate_fichas(fichas_raw)
        report["families"]["fichas.jsonl"] = {
            "raw": len(fichas_raw),
            "valid": len(fichas_res.valid),
            "dropped": fichas_res.dropped,
            "error_sample": fichas_res.errors[:10],
            "error_count": len(fichas_res.errors),
        }

    counts = {
        "noticias.csv": len(news.valid),
        "indicadores.csv": len(indicators.valid),
        "eventos.geojson": len(events.valid),
    }
    if (processed / "fichas.jsonl").exists():
        counts["fichas.jsonl"] = sum(
            1 for line in (processed / "fichas.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()
        )
    manifest = manifest_mod.build_manifest(processed, counts, queries, report["source"])
    manifest_mod.write_manifest(processed, manifest)
    report["manifest"] = manifest

    try:
        from evidentia.db import init_db

        init_db()
        report["db"] = _upsert_db(news.valid, indicators.valid, events.valid)
    except Exception as exc:
        report["warnings"].append(f"db upsert skipped: {exc}")
        logger.exception("DB upsert failed — files-only mode")

    # Post-ingest: vector indexing (best-effort; Qdrant may be down).
    try:
        from evidentia.retrieval import indexing

        report["index"] = {
            "news": indexing.index_news(news.valid),
            "indicators": indexing.index_indicators(indicators.valid),
        }
    except Exception as exc:
        report["warnings"].append(f"indexing skipped: {exc}")
        logger.warning("Indexing skipped: %s", exc)

    # Post-ingest: light graph build (best-effort).
    try:
        from sqlmodel import Session

        from evidentia.db import get_engine
        from evidentia.graph import relations as rel_mod
        from evidentia.graph.graph_service import persist_graph

        enriched, relations = rel_mod.build_article_relations(news.valid)
        with Session(get_engine()) as session:
            report["graph"] = persist_graph(
                session,
                enriched,
                relations,
                indicators=indicators.valid,
                events=events.valid,
            )
    except Exception as exc:
        report["warnings"].append(f"graph skipped: {exc}")
        logger.warning("Graph build skipped: %s", exc)

    # Post-ingest: auto-generate and persist prioritised ranking inbox.
    try:
        from sqlmodel import Session

        from evidentia.db import get_engine
        from evidentia.scoring.ranking_service import generate_and_persist_inbox

        with Session(get_engine()) as session:
            report["ranking_inbox"] = generate_and_persist_inbox(session)
    except Exception as exc:
        report["warnings"].append(f"ranking inbox generation skipped: {exc}")
        logger.warning("Ranking inbox generation skipped: %s", exc)

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    (processed / "quality_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    return report
