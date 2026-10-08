"""Tests for Modo Jurado API endpoints (/jurado/pruebas, /jurado/metricas)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from evidentia import models
from evidentia.auth.dependencies import get_current_user
from evidentia.main import create_app


def _auth_client() -> TestClient:
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


def test_jurado_metricas_endpoint() -> None:
    client = _auth_client()
    resp = client.get("/jurado/metricas")
    assert resp.status_code == 200
    data = resp.json()
    assert data["disponible"] is True
    assert "tabla" in data
    assert len(data["tabla"]) >= 5
    # Verify metric keys
    metricas = [row["metrica"] for row in data["tabla"]]
    assert any("Respuestas sustentadas" in m for m in metricas)
    assert any("Abstención correcta" in m for m in metricas)
    assert any("Cobertura de citas" in m for m in metricas)


def test_jurado_pruebas_get_and_post() -> None:
    client = _auth_client()

    # GET pruebas
    resp = client.get("/jurado/pruebas")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 10
    assert len(data["filas"]) == 10
    assert all(f["estado"] in ("verde", "rojo") for f in data["filas"])

    # POST pruebas (live runner)
    resp_post = client.post("/jurado/pruebas")
    assert resp_post.status_code == 200
    post_data = resp_post.json()
    assert post_data["total"] == 10
    assert post_data["verdes"] == 10
    assert all(f["estado"] == "verde" for f in post_data["filas"])
