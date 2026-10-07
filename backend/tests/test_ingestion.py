"""Fase 2 tests: validators, manifest, seed-mode pipeline, ingest endpoints."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from fastapi.testclient import TestClient

from evidentia.ingestion import manifest as manifest_mod
from evidentia.ingestion import validators
from evidentia.ingestion.pipeline import run_ingestion
from evidentia.main import create_app


def _write_tiny_seed(seed_dir: Path) -> None:
    seed_dir.mkdir(parents=True, exist_ok=True)
    with (seed_dir / "noticias.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "id_noticia", "titulo", "url", "medio", "idioma",
            "fecha_publicacion", "fecha_deteccion", "fecha_extraccion",
            "tema", "origen", "alcance_texto",
        ])
        w.writeheader()
        # valid row
        w.writerow({
            "titulo": "Canal amplía capacidad", "url": "https://example.com/canal",
            "medio": "TVN", "idioma": "es",
            "fecha_publicacion": "2026-10-01T12:00:00Z",
            "fecha_deteccion": "2026-10-01T12:05:00Z",
            "fecha_extraccion": "2026-10-06T00:00:00Z",
            "tema": "logística", "origen": "tvn", "alcance_texto": "titular",
        })
        # T01: invalid dates + nulls must not block the load
        w.writerow({
            "titulo": "Dato sin fecha", "url": "https://example.com/sin-fecha",
            "medio": "", "idioma": "es",
            "fecha_publicacion": "not-a-date", "fecha_deteccion": "",
            "fecha_extraccion": "2026-10-06T00:00:00Z",
            "tema": "", "origen": "gdelt", "alcance_texto": "titular",
        })
    with (seed_dir / "indicadores.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "pais_iso3", "indicador_id", "anio", "valor", "unidad",
            "fuente_url", "fecha_extraccion", "licencia",
        ])
        w.writeheader()
        w.writerow({
            "pais_iso3": "PAN", "indicador_id": "NY.GDP.MKTP.KD.ZG", "anio": "2024",
            "valor": "2.74", "unidad": "% anual",
            "fuente_url": "https://api.worldbank.org",
            "fecha_extraccion": "2026-10-06T00:00:00Z", "licencia": "CC BY 4.0",
        })
        w.writerow({  # null value kept explicit
            "pais_iso3": "PAN", "indicador_id": "SL.UEM.TOTL.ZS", "anio": "2024",
            "valor": "", "unidad": "%",
            "fuente_url": "https://api.worldbank.org",
            "fecha_extraccion": "2026-10-06T00:00:00Z", "licencia": "CC BY 4.0",
        })
    (seed_dir / "eventos.geojson").write_text(
        json.dumps({
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature", "id": "us123",
                "geometry": {"type": "Point", "coordinates": [-79.5, 8.9]},
                "properties": {
                    "mag": 4.5, "time": "2024-05-01T00:00:00Z",
                    "updated": "2024-05-02T00:00:00Z", "depth": 10.0,
                    "place": "Azuerro", "status": "reviewed",
                    "url": "https://earthquake.usgs.gov/us123",
                },
            }],
        }),
        encoding="utf-8",
    )


# ── Validators ─────────────────────────────────────────────────────────────

def test_news_invalid_dates_kept_with_errors() -> None:
    res = validators.validate_news([{
        "titulo": "t", "url": "https://example.com/x", "medio": "m",
        "fecha_publicacion": "bogus", "origen": "gdelt",
    }])
    assert len(res.valid) == 1
    assert res.valid[0]["fecha_publicacion"] is None
    assert res.valid[0]["id_noticia"].startswith("gdelt-")
    assert any("fecha_publicacion" in e["reason"] for e in res.errors)


def test_news_drops_missing_url_and_duplicates() -> None:
    rows = [
        {"titulo": "sin url", "url": ""},
        {"titulo": "a", "url": "https://example.com/a", "medio": "m"},
        {"titulo": "a dup", "url": "https://example.com/a", "medio": "m"},
    ]
    res = validators.validate_news(rows)
    assert len(res.valid) == 1
    assert res.dropped == 2


def test_indicators_keep_null_values() -> None:
    res = validators.validate_indicators([{
        "pais_iso3": "pan", "indicador_id": "X", "anio": "2024", "valor": "",
    }])
    assert len(res.valid) == 1
    assert res.valid[0]["valor"] is None
    assert res.valid[0]["pais_iso3"] == "PAN"


def test_events_invalid_numerics_nulled() -> None:
    res = validators.validate_events([{"id": "e1", "magnitude": "big"}])
    assert len(res.valid) == 1
    assert res.valid[0]["magnitude"] is None
    assert res.errors


# ── Manifest ───────────────────────────────────────────────────────────────

def test_manifest_hashes_verify(tmp_path: Path) -> None:
    d = tmp_path / "processed"
    d.mkdir()
    (d / "noticias.csv").write_text("a", encoding="utf-8")
    (d / "indicadores.csv").write_text("b", encoding="utf-8")
    (d / "eventos.geojson").write_text("c", encoding="utf-8")
    m = manifest_mod.build_manifest(d, {}, {"q": 1}, source="seed")
    assert m["archivos"]["noticias.csv"]["sha256"] == manifest_mod.sha256_file(d / "noticias.csv")
    assert m["fecha_corte_UTC"]
    out = manifest_mod.write_manifest(d, m)
    assert json.loads(out.read_text(encoding="utf-8"))["version"] == "v1"


# ── Pipeline (seed mode, sqlite) ───────────────────────────────────────────

def test_pipeline_seed_mode_end_to_end(tmp_path: Path) -> None:
    seed = tmp_path / "seed"
    data = tmp_path / "data"
    _write_tiny_seed(seed)

    report = run_ingestion(use_seed=True, data_dir=data, seed_dir=seed)

    assert report["source"] == "seed"
    assert report["families"]["noticias.csv"]["valid"] == 2  # T01 row kept
    assert report["families"]["indicadores.csv"]["valid"] == 2
    assert report["families"]["eventos.geojson"]["valid"] == 1
    assert report["db"] == {"news_articles": 2, "indicators": 2, "geo_events": 1}
    assert (data / "processed" / "manifest.json").exists()
    assert (data / "processed" / "quality_report.json").exists()

    # Null indicator value survived the round trip through the DB.
    from sqlmodel import Session, select

    from evidentia import models
    from evidentia.db import get_engine

    with Session(get_engine()) as session:
        rows = session.exec(select(models.Indicator)).all()
        assert sorted(r.valor is None for r in rows) == [False, True]


# ── API ────────────────────────────────────────────────────────────────────

def test_api_ingest_sync_and_quality_report(tmp_path: Path, monkeypatch) -> None:
    seed = tmp_path / "seed"
    _write_tiny_seed(seed)
    monkeypatch.setenv("SEED_DIR", str(seed))

    from evidentia.config import reset_settings
    from evidentia.db import reset_engine

    reset_settings()
    reset_engine()
    client = TestClient(create_app(), raise_server_exceptions=False)

    resp = client.post("/ingest/run", params={"sync": True, "use_seed": True})
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "done"
    assert resp.json()["report"]["families"]["noticias.csv"]["valid"] == 2

    resp = client.get("/ingest/quality-report")
    assert resp.status_code == 200
    assert resp.json()["source"] == "seed"
