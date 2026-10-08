"""Tests for the evidence item lookup endpoints (/evidence/item)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session

from evidentia import models
from evidentia.db import get_engine, init_db
from evidentia.main import create_app


def _auth_client() -> TestClient:
    from evidentia.auth.dependencies import get_current_user
    app = create_app()
    admin = models.User(
        id=1, email="admin@vertexdc.com", nombre="Admin",
        role="Super Admin", org_id="VERTEXdc", is_active=True, hashed_password=""
    )
    app.dependency_overrides[get_current_user] = lambda: admin
    return TestClient(app, raise_server_exceptions=False)


def _seed_test_data() -> dict:
    init_db()
    now = datetime.now(timezone.utc)
    with Session(get_engine()) as session:
        # 1. News
        news = models.NewsArticle(
            id_noticia="noticia-test-1",
            titulo="Canal de Panamá amplía calado en lago Gatún",
            url="https://tvn-2.com/nacionales/canal-amplia-calado_123.html",
            medio="TVN Noticias",
            fecha_publicacion=now,
            tema="Economía",
            alcance_texto="extracto",
            agencia_primaria="EFE",
        )
        session.add(news)

        # 2. Indicator
        ind = models.Indicator(
            pais_iso3="PAN",
            indicador_id="NY.GDP.MKTP.KD.ZG",
            anio=2023,
            valor=7.3,
            unidad="%",
            fuente_url="https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG?locations=PA",
            licencia="CC BY 4.0",
        )
        session.add(ind)

        # 3. GeoEvent
        event = models.GeoEvent(
            event_id="usgs-panama-quake-1",
            magnitude=5.4,
            depth=12.5,
            place="34 km S of Coiba, Panama",
            time=now,
            url="https://earthquake.usgs.gov/earthquakes/eventpage/usgs-panama-quake-1",
            status="reviewed",
        )
        session.add(event)

        # 4. Entity & Relation
        entity = models.Entity(
            nombre="Autoridad del Canal de Panamá",
            tipo="ORG",
            normalizado="autoridad del canal de panama",
        )
        session.add(entity)
        session.flush()

        rel = models.Relation(
            origen_tipo="news",
            origen_id=news.id_noticia,
            destino_tipo="entity",
            destino_id=str(entity.id),
            tipo="mentions",
            peso=0.8,
        )
        session.add(rel)

        # 5. Case
        case_obj = models.Case(
            titulo="Impacto de calado en tránsito comercial",
            modalidad="tvn",
            estado="nuevo",
            queries=["Canal de Panamá", "lago Gatún"],
        )
        session.add(case_obj)
        session.commit()
        session.refresh(entity)
        session.refresh(case_obj)

        return {
            "news_id": news.id_noticia,
            "indicator_key": f"{ind.pais_iso3}:{ind.indicador_id}:{ind.anio}",
            "indicator_id": ind.indicador_id,
            "event_id": event.event_id,
            "entity_id": str(entity.id),
            "entity_name": entity.nombre,
            "case_id": str(case_obj.id),
        }


def test_resolve_news_item() -> None:
    data = _seed_test_data()
    client = _auth_client()

    # Via path parameter
    resp = client.get(f"/evidence/item/news/{data['news_id']}")
    assert resp.status_code == 200, resp.text
    item = resp.json()
    assert item["tipo"] == "news"
    assert item["id"] == data["news_id"]
    assert "Canal de Panamá" in item["titulo"]
    assert item["fuente_nombre"] == "TVN Noticias"
    assert "https://tvn-2.com" in item["url"]
    assert item["detalles"]["agencia_primaria"] == "EFE"
    assert len(item["relaciones"]) >= 1

    # Via query parameter
    resp_query = client.get("/evidence/item", params={"tipo": "news", "id": data["news_id"]})
    assert resp_query.status_code == 200
    assert resp_query.json()["id"] == data["news_id"]


def test_resolve_indicator_item() -> None:
    data = _seed_test_data()
    client = _auth_client()

    # Via composite key
    resp = client.get(f"/evidence/item/indicator/{data['indicator_key']}")
    assert resp.status_code == 200, resp.text
    item = resp.json()
    assert item["tipo"] == "indicator"
    assert "Panamá" in item["titulo"]
    assert "PIB" in item["titulo"]
    assert item["detalles"]["valor"] == 7.3
    assert item["fuente_nombre"] == "Banco Mundial (World Bank Open Data)"

    # Via indicator_id only
    resp2 = client.get(f"/evidence/item/indicator/{data['indicator_id']}")
    assert resp2.status_code == 200
    assert resp2.json()["detalles"]["indicador_id"] == data["indicator_id"]


def test_resolve_event_item() -> None:
    data = _seed_test_data()
    client = _auth_client()

    resp = client.get(f"/evidence/item/event/{data['event_id']}")
    assert resp.status_code == 200, resp.text
    item = resp.json()
    assert item["tipo"] == "event"
    assert item["detalles"]["magnitude"] == 5.4
    assert "Coiba" in item["titulo"]
    assert "USGS" in item["fuente_nombre"]


def test_resolve_entity_and_case() -> None:
    data = _seed_test_data()
    client = _auth_client()

    # Entity
    resp_entity = client.get(f"/evidence/item/entity/{data['entity_id']}")
    assert resp_entity.status_code == 200
    item = resp_entity.json()
    assert item["tipo"] == "entity"
    assert item["detalles"]["nombre"] == data["entity_name"]
    assert len(item["relaciones"]) >= 1

    # Case
    resp_case = client.get(f"/evidence/item/case/{data['case_id']}")
    assert resp_case.status_code == 200
    assert resp_case.json()["tipo"] == "case"


def test_not_found_and_invalid_type() -> None:
    init_db()
    client = _auth_client()
    assert client.get("/evidence/item/news/non-existent-id").status_code == 404
    assert client.get("/evidence/item/unknown_type/123").status_code == 400


def test_get_global_graph() -> None:
    data = _seed_test_data()
    client = _auth_client()
    resp = client.get("/evidence/graph")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "nodes" in body
    assert "links" in body
    assert body["total_nodes"] > 0
    assert body["total_links"] > 0
    node_ids = {n["id"] for n in body["nodes"]}
    assert f"news:{data['news_id']}" in node_ids
    assert f"entity:{data['entity_id']}" in node_ids

