"""Fase 4 tests: ranking, cases, evidence tree and brief endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session

from evidentia import models
from evidentia.db import get_engine, init_db
from evidentia.main import create_app


def _seed_news() -> None:
    init_db()
    now = datetime.now(timezone.utc)
    with Session(get_engine()) as session:
        session.add(models.NewsArticle(
            id_noticia="g1", titulo="Panamá aprueba ampliación del Canal",
            url="https://example.com/g1", medio="Medio Uno",
            fecha_publicacion=now, grupo_evento_id="evt-1",
        ))
        session.add(models.NewsArticle(
            id_noticia="g2", titulo="Aprueban ampliación del Canal en Panamá",
            url="https://example.com/g2", medio="La Local",
            fecha_publicacion=now, grupo_evento_id="evt-1",
            agencia_primaria="EFE",
        ))
        session.add(models.NewsArticle(
            id_noticia="s1", titulo="Clima soleado en la capital",
            url="https://example.com/s1", medio="Otro",
            fecha_publicacion=now,
        ))
        session.commit()


def test_ranking_orders_and_explains() -> None:
    _seed_news()
    client = TestClient(create_app(), raise_server_exceptions=False)
    resp = client.get("/ranking", params={"modalidad": "tvn"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["rules_version"] == "v1"
    assert body["count"] == 2  # one group + one singleton
    first, second = body["items"]
    assert first["id"] == "evt-1"  # Panama+theme outranks off-topic
    assert first["P"] >= second["P"]
    assert set(first["components"]) == {"R", "I", "U", "N", "E"}
    assert first["dedup"]["primary_sources"] == 2
    assert first["band"] in ("bajo", "medio", "alto")


def test_case_lifecycle_evidence_notes_tree() -> None:
    _seed_news()
    client = TestClient(create_app(), raise_server_exceptions=False)

    resp = client.post("/cases", json={"titulo": "Caso Canal", "modalidad": "tvn"})
    assert resp.status_code == 201, resp.text
    case_id = resp.json()["id"]

    resp = client.post(f"/cases/{case_id}/evidence", json={
        "fuente_tipo": "news", "fuente_id": "g1", "nota": "respaldo principal",
    })
    assert resp.status_code == 201, resp.text

    resp = client.get(f"/cases/{case_id}")
    assert len(resp.json()["evidence"]) == 1

    resp = client.patch(f"/cases/{case_id}", json={"estado": "bogus"})
    assert resp.status_code == 422
    resp = client.patch(f"/cases/{case_id}", json={"estado": "en_revision"})
    assert resp.json()["estado"] == "en_revision"

    resp = client.post(f"/cases/{case_id}/notes", json={
        "autor": "editora", "estado_revision": "requiere_evidencia",
        "texto": "Falta cifra oficial del Canal.",
    })
    assert resp.status_code == 201, resp.text
    assert client.get(f"/cases/{case_id}").json()["estado"] == "requiere_evidencia"

    resp = client.get(f"/cases/{case_id}/tree")
    assert resp.status_code == 200, resp.text
    kinds = {(n["tipo"], n["id"]) for n in resp.json()["nodes"]}
    assert ("case", str(case_id)) in kinds and ("news", "g1") in kinds

    resp = client.get("/evidence/tree", params={"tipo": "news", "id": "g1"})
    assert resp.status_code == 200
    assert resp.json()["root"] == {"tipo": "news", "id": "g1"}


def test_brief_abstains_without_key_and_renders_markdown() -> None:
    _seed_news()
    client = TestClient(create_app(), raise_server_exceptions=False)
    case_id = client.post("/cases", json={"titulo": "Caso Canal"}).json()["id"]
    client.post(f"/cases/{case_id}/evidence", json={
        "fuente_tipo": "news", "fuente_id": "g1",
    })

    resp = client.post(f"/cases/{case_id}/brief")
    assert resp.status_code == 200, resp.text
    assert resp.json()["abstained"] is True  # no TOGETHER_API_KEY in tests

    resp = client.post(f"/cases/{case_id}/brief", params={"formato": "markdown"})
    assert resp.status_code == 200
    assert "text/markdown" in resp.headers["content-type"]
    assert "ABSTENCIÓN" in resp.text
