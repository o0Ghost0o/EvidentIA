"""Fase 1 smoke tests: app boots, health probes answer, models persist."""

from __future__ import annotations

import os

# Force sqlite before importing anything that reads settings/engine.
os.environ["DATABASE_URL"] = "sqlite://"

from fastapi.testclient import TestClient  # noqa: E402

from evidentia import models  # noqa: E402, F401
from evidentia.db import get_engine, init_db  # noqa: E402
from evidentia.main import create_app  # noqa: E402
from sqlmodel import Session, SQLModel  # noqa: E402


def test_health_ok() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "evidentia"


def test_ready_reports_degraded_without_services() -> None:
    client = TestClient(create_app(), raise_server_exceptions=False)
    resp = client.get("/ready")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in ("ok", "degraded")
    assert set(body["checks"]) == {"postgres", "qdrant", "redis"}


def test_models_roundtrip_sqlite() -> None:
    SQLModel.metadata.create_all(get_engine())
    init_db()
    with Session(get_engine()) as session:
        article = models.NewsArticle(
            id_noticia="seed-001",
            titulo="Titular de prueba",
            url="https://example.com/1",
            medio="TVN",
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        assert article.id is not None
        assert article.alcance_texto == "titular"
