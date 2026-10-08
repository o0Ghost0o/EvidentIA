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


def _auth_client(app=None) -> TestClient:
    from evidentia.auth.dependencies import get_current_user
    app = app or create_app()
    admin = models.User(id=1, email="admin@vertexdc.com", nombre="Admin", role="Super Admin", org_id="VERTEXdc", is_active=True, hashed_password="")
    app.dependency_overrides[get_current_user] = lambda: admin
    return TestClient(app, raise_server_exceptions=False)


def test_unauthenticated_requests_are_blocked() -> None:
    _seed_news()
    client = TestClient(create_app(), raise_server_exceptions=False)
    assert client.get("/ranking").status_code == 401
    assert client.post("/cases", json={"titulo": "Test"}).status_code == 401


def test_ranking_orders_and_explains() -> None:
    _seed_news()
    client = _auth_client()
    resp = client.get("/ranking", params={"modalidad": "tvn"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["rules_version"] == "v1.2"
    assert body["count"] == 2  # one group + one singleton
    first, second = body["items"]
    assert first["id"] == "evt-1"  # Panama+theme outranks off-topic
    assert first["P"] >= second["P"]
    assert set(first["components"]) == {"R", "I", "U", "N", "E"}
    assert first["dedup"]["primary_sources"] == 2
    assert first["band"] in ("bajo", "medio", "alto")


def test_case_lifecycle_evidence_notes_tree() -> None:
    _seed_news()
    client = _auth_client()

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

    # Test flags and activity flags
    resp_flags = client.post(f"/cases/{case_id}/flags", json={"flag": "Prioritario"})
    assert resp_flags.status_code == 200
    assert "Prioritario" in resp_flags.json()["flags"]
    act_flag_ids = {af["id"] for af in resp_flags.json()["activity_flags"]}
    assert "custom-Prioritario" in act_flag_ids
    assert "action-evidence-linked" in act_flag_ids
    assert "source-news" in act_flag_ids

    # Remove flag
    resp_del_flag = client.delete(f"/cases/{case_id}/flags/Prioritario")
    assert resp_del_flag.status_code == 200
    assert "Prioritario" not in resp_del_flag.json()["flags"]

    resp = client.get("/evidence/tree", params={"tipo": "news", "id": "g1"})
    assert resp.status_code == 200
    assert resp.json()["root"] == {"tipo": "news", "id": "g1"}


def test_evidence_accepts_document_source_type() -> None:
    # Step 2 "Evidencia" links documents (primary sources) alongside news/indicator/event.
    init_db()
    client = _auth_client()
    case_id = client.post("/cases", json={"titulo": "Caso con documento"}).json()["id"]

    resp = client.post(f"/cases/{case_id}/evidence", json={
        "fuente_tipo": "document", "fuente_id": "res-1187", "rol": "Respalda",
    })
    assert resp.status_code == 201, resp.text

    detail = client.get(f"/cases/{case_id}").json()
    assert any(e["fuente_tipo"] == "document" for e in detail["evidence"])
    assert "source-document" in {af["id"] for af in detail["activity_flags"]}


def test_brief_abstains_without_key_and_renders_markdown(monkeypatch) -> None:
    monkeypatch.setenv("TOGETHER_API_KEY", "")
    from evidentia.config import reset_settings

    reset_settings()
    _seed_news()
    client = _auth_client()
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


def test_create_case_with_evidence_ids_links_sources_and_relations() -> None:
    _seed_news()
    client = _auth_client()

    resp = client.post("/cases", json={
        "titulo": "Ampliación del Canal",
        "modalidad": "tvn",
        "evidence_ids": ["g1", "g2"],
    })
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert len(body["evidence"]) == 2
    ev_ids = {e["fuente_id"] for e in body["evidence"]}
    assert ev_ids == {"g1", "g2"}

    # Verify tree contains case node, both news nodes and relations
    tree_resp = client.get(f"/cases/{body['id']}/tree")
    assert tree_resp.status_code == 200, tree_resp.text
    tree = tree_resp.json()
    node_ids = {n["id"] for n in tree["nodes"]}
    assert str(body["id"]) in node_ids
    assert "g1" in node_ids
    assert "g2" in node_ids
    assert len(tree["edges"]) >= 2


def test_case_auto_healing_populates_empty_case_from_matching_articles() -> None:
    _seed_news()
    client = _auth_client()

    # Create empty case without evidence_ids, but with matching title
    resp = client.post("/cases", json={
        "titulo": "Panamá aprueba ampliación del Canal",
        "modalidad": "tvn",
        "flags": ["evt-1"],
    })
    assert resp.status_code == 201, resp.text
    body = resp.json()
    case_id = body["id"]

    # When querying detail, auto-healing populates both articles from the event group
    detail_resp = client.get(f"/cases/{case_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert len(detail["evidence"]) == 2
    ev_ids = {e["fuente_id"] for e in detail["evidence"]}
    assert ev_ids == {"g1", "g2"}

    # When querying tree, the tree has both news nodes and edges
    tree_resp = client.get(f"/cases/{case_id}/tree")
    assert tree_resp.status_code == 200
    tree = tree_resp.json()
    node_ids = {n["id"] for n in tree["nodes"]}
    assert "g1" in node_ids
    assert "g2" in node_ids
    assert len(tree["edges"]) >= 2

