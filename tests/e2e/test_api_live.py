"""End-to-End API testing suite targeting dev-evidentia-api.vertexdc.com.

Validates health, readiness, ranking, cases lifecycle, evidence graph,
and brief generation against the live deployed API.
"""

from __future__ import annotations

import os
import time
import httpx
import pytest

API_BASE_URL = os.getenv("E2E_API_URL", "https://dev-evidentia-api.vertexdc.com").rstrip("/")
CLIENT_TIMEOUT = float(os.getenv("E2E_TIMEOUT", "20.0"))


@pytest.fixture(scope="session")
def client() -> httpx.Client:
    """HTTP client configured for E2E testing with SSL verify and generous timeout."""
    with httpx.Client(base_url=API_BASE_URL, timeout=CLIENT_TIMEOUT, follow_redirects=True) as c:
        yield c


def test_e2e_api_health(client: httpx.Client) -> None:
    """Verify live GET /health responds with 200 OK and expected service metadata."""
    try:
        response = client.get("/health")
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        pytest.fail(f"Could not connect to {API_BASE_URL}/health: {exc}")

    if response.status_code in (502, 503, 525):
        pytest.skip(f"Deploy still warming up at {API_BASE_URL} (status {response.status_code})")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data.get("status") == "ok"
    assert data.get("service") == "evidentia"
    assert "version" in data


def test_e2e_api_ready(client: httpx.Client) -> None:
    """Verify live GET /ready probe responds with dependency checks."""
    try:
        response = client.get("/ready")
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        pytest.fail(f"Could not connect to {API_BASE_URL}/ready: {exc}")

    if response.status_code in (502, 503, 525):
        pytest.skip(f"Deploy still warming up at {API_BASE_URL} (status {response.status_code})")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert isinstance(data["checks"], dict)


def test_e2e_api_ranking_tvn(client: httpx.Client) -> None:
    """Verify live GET /ranking returns prioritized news items with scoring components."""
    try:
        response = client.get("/ranking", params={"modalidad": "tvn", "limit": 10})
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        pytest.fail(f"Could not connect to {API_BASE_URL}/ranking: {exc}")

    if response.status_code in (502, 503, 525):
        pytest.skip(f"Deploy still warming up at {API_BASE_URL} (status {response.status_code})")

    assert response.status_code == 200
    data = response.json()
    assert "rules_version" in data
    assert "items" in data
    assert isinstance(data["items"], list)

    if len(data["items"]) > 0:
        first = data["items"][0]
        assert "id" in first
        assert "titulo" in first
        assert "P" in first
        assert "components" in first
        assert "R" in first["components"]
        assert "U" in first["components"]
        assert "C" in first["components"]
        assert "N" in first["components"]


def test_e2e_api_case_lifecycle_and_tree(client: httpx.Client) -> None:
    """Verify complete case lifecycle on live API: create, fetch, add note, view tree."""
    unique_title = f"E2E Test Investigation {int(time.time())}"
    create_payload = {
        "titulo": unique_title,
        "modalidad": "tvn",
        "queries": ["canal de panama", "economia"],
        "flags": ["e2e-automated"],
    }

    try:
        res_create = client.post("/cases", json=create_payload)
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        pytest.fail(f"Could not connect to {API_BASE_URL}/cases: {exc}")

    if res_create.status_code in (502, 503, 525):
        pytest.skip(f"Deploy still warming up at {API_BASE_URL} (status {res_create.status_code})")

    assert res_create.status_code == 201, f"Failed to create case: {res_create.text}"
    case_data = res_create.json()
    case_id = case_data["id"]
    assert case_data["titulo"] == unique_title

    # 1. Fetch case by ID
    res_get = client.get(f"/cases/{case_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == case_id

    # 2. Add verification note
    note_payload = {
        "autor": "E2E Test Runner",
        "estado_revision": "en_revision",
        "texto": "Nota de verificación creada automáticamente por test E2E.",
    }
    res_note = client.post(f"/cases/{case_id}/notes", json=note_payload)
    assert res_note.status_code == 201
    assert res_note.json()["estado_revision"] == "en_revision"

    # 3. Retrieve evidence tree
    res_tree = client.get(f"/cases/{case_id}/tree?depth=3")
    assert res_tree.status_code == 200
    tree_data = res_tree.json()
    assert "root" in tree_data
    assert "nodes" in tree_data
    assert "edges" in tree_data
    assert tree_data["root"]["id"] == str(case_id)


def test_e2e_api_case_brief_generation(client: httpx.Client) -> None:
    """Verify editorial brief endpoint on live API returns valid structure (brief or structured abstention)."""
    unique_title = f"E2E Test Editorial Brief {int(time.time())}"
    res_create = client.post("/cases", json={"titulo": unique_title, "modalidad": "tvn"})

    if res_create.status_code in (502, 503, 525):
        pytest.skip(f"Deploy still warming up at {API_BASE_URL} (status {res_create.status_code})")

    assert res_create.status_code == 201
    case_id = res_create.json()["id"]

    res_brief = client.post(f"/cases/{case_id}/brief")
    assert res_brief.status_code == 200
    brief_data = res_brief.json()
    assert (
        "abstained" in brief_data
        or "paquete" in brief_data
        or "brief" in brief_data
        or "estado" in brief_data
        or "texto" in brief_data
    )
