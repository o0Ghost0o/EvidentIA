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
    assert resp.json()["sentence_breakdown"] == []
    assert resp.json()["sentences"] == []

    resp = client.post(f"/cases/{case_id}/brief", params={"formato": "markdown"})
    assert resp.status_code == 200
    assert "text/markdown" in resp.headers["content-type"]
    assert "ABSTENCIÓN" in resp.text


def test_brief_emits_sentence_breakdown_and_claim_support(monkeypatch) -> None:
    from evidentia.briefs import tvn
    from evidentia.generation.synthesizer import Synthesiser

    _seed_news()
    client = _auth_client()
    case_id = client.post("/cases", json={"titulo": "Caso Canal", "modalidad": "tvn"}).json()["id"]
    client.post(f"/cases/{case_id}/evidence", json={
        "fuente_tipo": "news", "fuente_id": "g1",
    })

    reply = """## Título propuesto
Canal
## Brief
[HECHO] Canal amplía tránsito [g1:titulo]. [INFERENCIA] Podría dinamizar la economía regional.
## Enfoque de interés público
Impacto
## Preguntas de investigación
1. a
2. b
3. c
## Fuentes y verificaciones pendientes
- Prensa
## Guion 45-60 segundos
[DECLARACIÓN] "El flujo se mantiene constante", afirmó el administrador [g1:titulo].
## Copy digital
Canal ampliado.
"""
    class _MockClient:
        def complete(self, system: str, user: str, max_tokens: int = 1500) -> str:
            return reply

    mock_synth = Synthesiser(client=_MockClient())
    monkeypatch.setattr(tvn, "Synthesiser", lambda: mock_synth)

    resp = client.post(f"/cases/{case_id}/brief")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["abstained"] is False
    assert "sentence_breakdown" in data
    assert "sentences" in data
    assert len(data["sentence_breakdown"]) >= 3

    # Supported hecho with citation
    hecho_sents = [s for s in data["sentence_breakdown"] if s["class"] == "hecho"]
    assert len(hecho_sents) >= 1
    assert hecho_sents[0]["sin_respaldo"] is False
    assert "[g1:titulo]" in hecho_sents[0]["citations"]

    # Unsupported inferencia
    inf_sents = [s for s in data["sentence_breakdown"] if s["class"] == "inferencia"]
    assert len(inf_sents) >= 1
    assert inf_sents[0]["sin_respaldo"] is True
    assert inf_sents[0]["support_status"] == "sin respaldo"

    # Declaración
    dec_sents = [s for s in data["sentence_breakdown"] if s["class"] == "declaración"]
    assert len(dec_sents) >= 1
    assert dec_sents[0]["sin_respaldo"] is False


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


def test_case_indicator_auto_healing_and_catalog():
    init_db()
    with Session(get_engine()) as session:
        session.add(models.Indicator(
            pais_iso3="PAN", indicador_id="FP.CPI.TOTL.ZG", anio=2023, valor=1.5, fuente="World Bank"
        ))
        session.add(models.Indicator(
            pais_iso3="PAN", indicador_id="FP.CPI.TOTL.ZG", anio=2024, valor=1.8, fuente="World Bank"
        ))
        session.commit()

    client = _auth_client()

    # Catalog endpoint returns indicator
    cat_resp = client.get("/cases/catalog")
    assert cat_resp.status_code == 200
    catalog = cat_resp.json()
    assert any(c["id"].startswith("PAN:FP.CPI.TOTL.ZG") for c in catalog)

    # Creating a case with ind topic flag auto-heals its evidence
    case_resp = client.post("/cases", json={
        "titulo": "Inflación Panamá",
        "modalidad": "tvn",
        "flags": ["topic_id:ind:PAN:FP.CPI.TOTL.ZG", "band:alto", "p:75.5"],
    })
    assert case_resp.status_code == 201
    cid = case_resp.json()["id"]

    detail_resp = client.get(f"/cases/{cid}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert len(detail["evidence"]) >= 2
    assert any("2024" in e["fuente_id"] for e in detail["evidence"])
    assert detail["evidence"][0]["fuente_tipo"] == "indicator"



