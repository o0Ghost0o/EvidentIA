"""Tests for Jury Demo Credentials and Multi-Role RBAC Enforcement.

Audits:
- Super Admin / Jurado (admin@tvn.com): Unrestricted access (jurado run, ingest, delete cases).
- Editor Jefe (editor@tvn.com): Editorial triage (cases, delete cases), blocked from live jurado run.
- Periodista (periodista@tvn.com): Investigation & leads, blocked from delete cases, ingest, and jurado run.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlmodel import Session

from evidentia import models
from evidentia.auth.dependencies import bootstrap_initial_admin
from evidentia.db import get_engine, init_db
from evidentia.main import create_app


def _get_client_and_seed() -> TestClient:
    init_db()
    with Session(get_engine()) as session:
        bootstrap_initial_admin(session)
    return TestClient(create_app(), raise_server_exceptions=False)


def test_demo_accounts_login_and_roles() -> None:
    client = _get_client_and_seed()

    # 1. Super Admin / Jurado
    resp_admin = client.post("/auth/login", json={
        "email": "admin@tvn.com",
        "password": "EvidentIA2026!",
    })
    assert resp_admin.status_code == 200, resp_admin.text
    data_admin = resp_admin.json()
    assert data_admin["user"]["role"] == "Super Admin"
    assert data_admin["user"]["nombre"] == "Super Admin / Jurado"

    # 2. Editor Jefe
    resp_editor = client.post("/auth/login", json={
        "email": "editor@tvn.com",
        "password": "EvidentIA2026!",
    })
    assert resp_editor.status_code == 200, resp_editor.text
    data_editor = resp_editor.json()
    assert data_editor["user"]["role"] == "Owner"
    assert data_editor["user"]["nombre"] == "Editor Jefe"

    # 3. Periodista
    resp_periodista = client.post("/auth/login", json={
        "email": "periodista@tvn.com",
        "password": "EvidentIA2026!",
    })
    assert resp_periodista.status_code == 200, resp_periodista.text
    data_periodista = resp_periodista.json()
    assert data_periodista["user"]["role"] == "Member"
    assert data_periodista["user"]["nombre"] == "Periodista de Redacción"


def test_rbac_permissions_matrix() -> None:
    client = _get_client_and_seed()

    # Login tokens
    token_admin = client.post("/auth/login", json={
        "email": "admin@tvn.com", "password": "EvidentIA2026!"
    }).json()["access_token"]
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    token_editor = client.post("/auth/login", json={
        "email": "editor@tvn.com", "password": "EvidentIA2026!"
    }).json()["access_token"]
    headers_editor = {"Authorization": f"Bearer {token_editor}"}

    token_periodista = client.post("/auth/login", json={
        "email": "periodista@tvn.com", "password": "EvidentIA2026!"
    }).json()["access_token"]
    headers_periodista = {"Authorization": f"Bearer {token_periodista}"}

    # 1. Periodista can create cases and access trees
    case_res = client.post(
        "/cases",
        json={"titulo": "Investigación periodística de prueba", "modalidad": "tvn"},
        headers=headers_periodista,
    )
    assert case_res.status_code == 201, case_res.text
    case_id = case_res.json()["id"]

    tree_res = client.get(f"/cases/{case_id}/tree", headers=headers_periodista)
    assert tree_res.status_code == 200

    # 2. Periodista CANNOT delete cases (requires Owner/Super Admin) -> 403
    del_forbidden = client.delete(f"/cases/{case_id}", headers=headers_periodista)
    assert del_forbidden.status_code == 403
    assert "access denied" in del_forbidden.json()["detail"].lower()

    # 3. Periodista CANNOT run bulk ingest -> 403
    ingest_forbidden = client.post("/ingest/run?sync=true", headers=headers_periodista)
    assert ingest_forbidden.status_code == 403

    # 4. Periodista CANNOT run live jurado acceptance suite -> 403
    jurado_forbidden = client.post("/jurado/pruebas", headers=headers_periodista)
    assert jurado_forbidden.status_code == 403

    # 5. Editor Jefe CAN read jurado reports, but CANNOT trigger live suite run (Super Admin only) -> 403
    assert client.get("/jurado/pruebas", headers=headers_editor).status_code == 200
    assert client.post("/jurado/pruebas", headers=headers_editor).status_code == 403

    # 6. Editor Jefe CAN delete cases (Owner permission) -> 204
    del_owner = client.delete(f"/cases/{case_id}", headers=headers_editor)
    assert del_owner.status_code == 204

    # 7. Super Admin CAN run live jurado acceptance suite -> 200
    jurado_allowed = client.post("/jurado/pruebas", headers=headers_admin)
    assert jurado_allowed.status_code == 200
