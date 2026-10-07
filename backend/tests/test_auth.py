"""Tests for security layer: dual JWT tokens (15m/7d), rotation, and RBAC."""

from __future__ import annotations

import jwt
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from evidentia import models
from evidentia.auth.security import create_access_token, decode_token, hash_password
from evidentia.db import get_engine, init_db
from evidentia.main import create_app


def _setup_db():
    init_db()
    with Session(get_engine()) as session:
        # Clear users and refresh tokens for isolated testing
        session.exec(select(models.RefreshToken)).all()
        for t in session.exec(select(models.RefreshToken)).all():
            session.delete(t)
        for u in session.exec(select(models.User)).all():
            session.delete(u)
        session.commit()


def test_auth_bootstrap_and_login_dual_jwt():
    _setup_db()
    client = TestClient(create_app(), raise_server_exceptions=False)

    # 1. Login triggers bootstrap of initial admin from secrets/env
    resp = client.post("/auth/login", json={
        "email": "admin@vertexdc.com",
        "password": "EvidentIA2026!",
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Check 15m access token & 7d refresh token
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["expires_in"] == 900  # 15 minutes
    assert data["refresh_expires_in"] == 604800  # 7 days
    assert data["user"]["email"] == "admin@vertexdc.com"
    assert data["user"]["role"] == "Super Admin"

    access_payload = decode_token(data["access_token"])
    assert access_payload["type"] == "access"
    assert access_payload["email"] == "admin@vertexdc.com"
    assert access_payload["role"] == "Super Admin"

    refresh_payload = decode_token(data["refresh_token"])
    assert refresh_payload["type"] == "refresh"
    assert refresh_payload["email"] == "admin@vertexdc.com"


def test_auth_invalid_credentials():
    _setup_db()
    client = TestClient(create_app(), raise_server_exceptions=False)

    # First trigger bootstrap
    client.post("/auth/bootstrap")

    resp = client.post("/auth/login", json={
        "email": "admin@vertexdc.com",
        "password": "wrong-password",
    })
    assert resp.status_code == 401
    assert "Incorrect email or password" in resp.json()["detail"]


def test_token_refresh_rotation_and_revocation():
    _setup_db()
    client = TestClient(create_app(), raise_server_exceptions=False)

    # Login
    login_resp = client.post("/auth/login", json={
        "email": "admin@vertexdc.com",
        "password": "EvidentIA2026!",
    })
    assert login_resp.status_code == 200
    first_refresh = login_resp.json()["refresh_token"]

    # Refresh
    refresh_resp = client.post("/auth/refresh", json={"refresh_token": first_refresh})
    assert refresh_resp.status_code == 200
    new_data = refresh_resp.json()
    second_refresh = new_data["refresh_token"]
    assert second_refresh != first_refresh
    assert new_data["expires_in"] == 900

    # Old refresh token MUST be revoked (anti-replay rotation)
    reused_resp = client.post("/auth/refresh", json={"refresh_token": first_refresh})
    assert reused_resp.status_code == 401
    assert "revoked" in reused_resp.json()["detail"].lower()

    # Second refresh works
    third_resp = client.post("/auth/refresh", json={"refresh_token": second_refresh})
    assert third_resp.status_code == 200


def test_auth_me_endpoint():
    _setup_db()
    client = TestClient(create_app(), raise_server_exceptions=False)

    login_resp = client.post("/auth/login", json={
        "email": "admin@vertexdc.com",
        "password": "EvidentIA2026!",
    })
    token = login_resp.json()["access_token"]

    # Access /auth/me with Bearer token
    me_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    user_info = me_resp.json()
    assert user_info["email"] == "admin@vertexdc.com"
    assert user_info["role"] == "Super Admin"

    # Access without token fails with 401
    unauth_resp = client.get("/auth/me")
    assert unauth_resp.status_code == 401


def test_logout_revokes_refresh_token():
    _setup_db()
    client = TestClient(create_app(), raise_server_exceptions=False)

    login_resp = client.post("/auth/login", json={
        "email": "admin@vertexdc.com",
        "password": "EvidentIA2026!",
    })
    refresh_tok = login_resp.json()["refresh_token"]

    logout_resp = client.post("/auth/logout", json={"refresh_token": refresh_tok})
    assert logout_resp.status_code == 204

    # Now refresh must fail
    refresh_resp = client.post("/auth/refresh", json={"refresh_token": refresh_tok})
    assert refresh_resp.status_code == 401
