"""Tests for multi-modal ranking inbox generation, scoring and persistence."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from fastapi.testclient import TestClient
from sqlmodel import Session

from evidentia import models
from evidentia.db import get_engine, init_db
from evidentia.main import create_app
from evidentia.scoring.ranking_service import (
    generate_and_persist_inbox,
    generate_inbox_topics,
)


def _seed_multimodal_data(session: Session) -> None:
    now = datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc)

    # 1. News
    session.add(
        models.NewsArticle(
            id_noticia="noticia_1",
            titulo="Panamá amplía operaciones del Canal y logística marítima",
            url="https://tvn-2.com/canal-1",
            medio="TVN Noticias",
            fecha_publicacion=now,
            origen="tvn",
            alcance_texto="completo",
            grupo_evento_id="evt-canal",
            agencia_primaria="TVN",
        )
    )
    session.add(
        models.NewsArticle(
            id_noticia="noticia_2",
            titulo="Nueva terminal en el Canal de Panamá impulsa comercio",
            url="https://prensa.com/canal-2",
            medio="La Prensa",
            fecha_publicacion=now,
            origen="prensa",
            alcance_texto="completo",
            grupo_evento_id="evt-canal",
            agencia_primaria="EFE",
        )
    )

    # 2. Indicators (series for PAN)
    for year, val in [(2021, 15.3), (2022, 10.8), (2023, 7.3), (2024, 2.5)]:
        session.add(
            models.Indicator(
                pais_iso3="PAN",
                indicador_id="NY.GDP.MKTP.KD.ZG",
                anio=year,
                valor=val,
                unidad="%",
                fuente_url="https://worldbank.org",
            )
        )
    for year, val in [(2023, 1.5), (2024, 1.2)]:
        session.add(
            models.Indicator(
                pais_iso3="PAN",
                indicador_id="FP.CPI.TOTL.ZG",
                anio=year,
                valor=val,
                unidad="%",
                fuente_url="https://worldbank.org",
            )
        )

    # 3. GeoEvents (USGS earthquakes)
    session.add(
        models.GeoEvent(
            event_id="us7000test1",
            magnitude=5.8,
            time=now,
            place="24 km S of Boca Chica, Panama",
            depth=12.0,
            status="reviewed",
            url="https://earthquake.usgs.gov/earthquakes/eventpage/us7000test1",
        )
    )
    session.add(
        models.GeoEvent(
            event_id="us7000test2",
            magnitude=4.2,
            time=now,
            place="45 km W of David, Chiriquí, Panama",
            depth=18.0,
            status="reviewed",
            url="https://earthquake.usgs.gov/earthquakes/eventpage/us7000test2",
        )
    )

    session.commit()


def _auth_client() -> TestClient:
    from evidentia.auth.dependencies import get_current_user

    app = create_app()
    admin = models.User(
        id=1,
        email="admin@vertexdc.com",
        nombre="Admin",
        role="Super Admin",
        org_id="VERTEXdc",
        is_active=True,
        hashed_password="",
    )
    app.dependency_overrides[get_current_user] = lambda: admin
    return TestClient(app, raise_server_exceptions=False)


def test_multimodal_topic_generation() -> None:
    init_db()
    with Session(get_engine()) as session:
        _seed_multimodal_data(session)

        # Generate topics: all
        res_all = generate_inbox_topics(session, modalidad="tvn", limit=500, tipo="all")
        assert res_all["counts_by_type"]["news"] == 1  # 1 group (evt-canal)
        assert res_all["counts_by_type"]["indicator"] == 2  # 2 series (GDP, CPI)
        assert res_all["counts_by_type"]["event"] == 2  # 2 seismic events
        assert res_all["count"] == 5

        # Check types present in items
        types = {it["tipo"] for it in res_all["items"]}
        assert types == {"news", "indicator", "event"}

        # Check filter: indicators only
        res_ind = generate_inbox_topics(session, modalidad="banca", limit=500, tipo="indicator")
        assert res_ind["count"] == 2
        for it in res_ind["items"]:
            assert it["tipo"] == "indicator"
            assert "PAN:" in it["id"]
            assert it["evidence_state"] == "suficiente"
            assert len(it["ids_fuente"]) >= 2

        # Check filter: events only
        res_geo = generate_inbox_topics(session, modalidad="tvn", limit=500, tipo="event")
        assert res_geo["count"] == 2
        for it in res_geo["items"]:
            assert it["tipo"] == "event"
            assert it["magnitude"] >= 4.0
            assert it["evidence_state"] == "suficiente"


def test_ranking_api_endpoint_multimodal() -> None:
    init_db()
    with Session(get_engine()) as session:
        _seed_multimodal_data(session)

    client = _auth_client()

    # Call /ranking with default limit=500 and all types
    resp = client.get("/ranking", params={"modalidad": "tvn", "limit": 500, "tipo": "all"})
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert "counts_by_type" in body
    assert body["counts_by_type"]["news"] >= 1
    assert body["counts_by_type"]["indicator"] >= 2
    assert body["counts_by_type"]["event"] >= 2
    assert len(body["items"]) == 5

    # Test filtering by tipo=event
    resp_evt = client.get("/ranking", params={"modalidad": "tvn", "tipo": "event"})
    assert resp_evt.status_code == 200
    body_evt = resp_evt.json()
    assert len(body_evt["items"]) == 2
    assert all(it["tipo"] == "event" for it in body_evt["items"])


def test_generate_and_persist_ranking_inbox() -> None:
    init_db()
    with Session(get_engine()) as session:
        _seed_multimodal_data(session)
        result = generate_and_persist_inbox(session)

    assert result["status"] == "success"
    assert result["counts"]["total"] == 5

    from evidentia import config
    settings = config.get_settings()
    processed_dir = config.resolve_data_path(Path(settings.data_dir) / "processed")
    persisted = processed_dir / "ranking_inbox.json"
    assert persisted.exists()
    data = json.loads(persisted.read_text(encoding="utf-8"))
    assert "modalidades" in data
    assert "tvn" in data["modalidades"]
    assert "banca" in data["modalidades"]
    assert data["counts"]["total"] == 5
