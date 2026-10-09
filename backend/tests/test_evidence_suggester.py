"""Tests for Evidence Suggester (RAG + GraphRAG + Contradiction detection)."""

from __future__ import annotations

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from evidentia import models
from evidentia.db import get_engine, init_db
from evidentia.main import create_app
from evidentia.retrieval.evidence_suggester import (
    detect_contradiction_signal,
    get_suggested_evidence,
)


def _seed_test_corpus() -> None:
    init_db()
    now = datetime.now(timezone.utc)
    with Session(get_engine()) as session:
        # Article 1: Official statement
        session.add(
            models.NewsArticle(
                id_noticia="ev-tarifa-1",
                titulo="ASEP aprueba incremento a tarifa eléctrica del 15% para el primer semestre",
                resumen="El regulador de servicios públicos confirmó el aumento tarifario de energía.",
                cuerpo="ASEP aprobó un incremento del 15% en las tarifas eléctricas residenciales.",
                url="https://example.com/asep-1",
                medio="La Prensa",
                fecha_publicacion=now,
            )
        )
        # Article 2: Opposing / denial statement
        session.add(
            models.NewsArticle(
                id_noticia="ev-tarifa-2",
                titulo="Gremios desmienten alza y aseguran que la ASEP comete un error en tarifa eléctrica",
                resumen="Representantes empresariales rechazan la medida y afirman que no habrá incremento.",
                cuerpo="El sector privado niega la validez técnica de la subida y desmiente al regulador.",
                url="https://example.com/asep-2",
                medio="TVN Noticias",
                fecha_publicacion=now,
            )
        )
        # Article 3: General context
        session.add(
            models.NewsArticle(
                id_noticia="ev-tarifa-3",
                titulo="Consumo energético en Panamá supera récord histórico por altas temperaturas",
                resumen="La demanda de electricidad creció de forma sostenida durante el verano.",
                cuerpo="El despacho de carga reportó picos de consumo de energía eléctrica.",
                url="https://example.com/asep-3",
                medio="Panamá América",
                fecha_publicacion=now,
            )
        )
        session.commit()


def _auth_client(app=None) -> TestClient:
    from evidentia.auth.dependencies import get_current_user

    app = app or create_app()
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


def test_detect_contradiction_signal_patterns() -> None:
    # Strong refutation pattern
    is_contra, reason = detect_contradiction_signal(
        candidate_text="Gremios desmienten al regulador y niegan aumento alguno",
        lead_query="ASEP anuncia aumento de tarifas",
    )
    assert is_contra is True
    assert reason is not None
    assert "desmient" in reason or "niega" in reason

    # Opposing polarity pair
    is_contra_pol, reason_pol = detect_contradiction_signal(
        candidate_text="Corte rechaza el contrato de concesión",
        lead_query="Gobierno aprueba contrato minero",
    )
    assert is_contra_pol is True
    assert "aprueba" in reason_pol or "rechaza" in reason_pol or "contrapuesta" in reason_pol

    # Neutral statements
    is_contra_neu, _ = detect_contradiction_signal(
        candidate_text="Gran desfile patrio en la cinta costera",
        lead_query="Panamá celebra fiestas patrias",
    )
    assert is_contra_neu is False


def test_suggested_evidence_for_query() -> None:
    _seed_test_corpus()
    with Session(get_engine()) as session:
        suggestions = get_suggested_evidence(
            session=session,
            query_text="tarifa eléctrica aumento asep",
            limit=10,
        )
        assert len(suggestions) > 0
        ids = [s["id"] for s in suggestions]
        assert any("tarifa" in i for i in ids)

        # Check structure
        sample = suggestions[0]
        assert "suggested_role" in sample
        assert "is_contradiction" in sample
        assert "similarity_score" in sample
        assert sample["suggested_role"] in ("contradiccion", "respaldo", "contexto")


def test_api_endpoints_suggested_evidence() -> None:
    _seed_test_corpus()
    client = _auth_client()

    # 1. Global query suggester
    resp = client.get("/cases/suggested-evidence", params={"q": "tarifa eléctrica"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(item["suggested_role"] in ("contradiccion", "respaldo", "contexto") for item in data)

    # 2. Case-specific suggester
    case_resp = client.post(
        "/cases",
        json={
            "titulo": "Crisis por tarifa eléctrica y descontento social",
            "modalidad": "tvn",
            "queries": ["tarifa eléctrica aumento asep"],
        },
    )
    assert case_resp.status_code == 201, case_resp.text
    case_id = case_resp.json()["id"]

    resp_case = client.get(f"/cases/{case_id}/suggested-evidence")
    assert resp_case.status_code == 200, resp_case.text
    case_data = resp_case.json()
    assert isinstance(case_data, list)
    assert len(case_data) > 0
