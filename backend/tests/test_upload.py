"""Unit tests for template downloads, file uploads, upload ID, and duplicate detection."""

import io
from fastapi.testclient import TestClient

from evidentia.main import create_app
from evidentia.db import init_db
from evidentia import models


def test_download_templates():
    init_db()
    app = create_app()
    from evidentia.auth.dependencies import get_current_user
    admin = models.User(id=1, email="admin@vertexdc.com", nombre="Admin", role="Super Admin", org_id="VERTEXdc", is_active=True, hashed_password="")
    app.dependency_overrides[get_current_user] = lambda: admin
    client = TestClient(app)

    for fam in ("noticias", "indicadores", "eventos", "fichas"):
        res = client.get(f"/ingest/templates/{fam}")
        assert res.status_code == 200
        assert len(res.content) > 0



def test_upload_news_with_duplicate_detection():
    init_db()
    app = create_app()
    from evidentia.auth.dependencies import get_current_user
    admin = models.User(id=1, email="admin@vertexdc.com", nombre="Admin", role="Super Admin", org_id="VERTEXdc", is_active=True, hashed_password="")
    app.dependency_overrides[get_current_user] = lambda: admin
    client = TestClient(app)

    csv_data = """id_noticia,titulo,url,medio,idioma,fecha_publicacion,fecha_deteccion,fecha_extraccion,tema,origen,alcance_texto
test-upl-1,Canal de Panama amplía calado,https://example.com/noticia-dup,TVN,es,2026-10-08T10:00:00Z,,,Economía,manual,titular
test-upl-2,Canal de Panama amplía calado copia,https://example.com/noticia-dup,TVN,es,2026-10-08T10:00:00Z,,,Economía,manual,titular
test-upl-3,Nueva inversion en infraestructura portuaria,https://example.com/noticia-3,La Prensa,es,2026-10-08T11:00:00Z,,,Economía,manual,titular
"""
    files = {"file": ("noticias_test.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    res = client.post("/ingest/upload?family=noticias", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["upload_id"].startswith("upl-")
    assert "timestamp" in data
    assert data["family"] == "noticias"
    assert data["total_rows"] == 3
    assert data["valid_rows"] == 2
    assert data["dropped_rows"] == 1
    assert data["duplicates_found"] is True
    assert data["duplicate_count"] == 1
    assert any("duplicate url" in str(d) for d in data["duplicate_details"])

    # Verify upload history endpoint
    h_res = client.get("/ingest/uploads")
    assert h_res.status_code == 200
    history = h_res.json()
    assert len(history) > 0
    assert history[0]["upload_id"] == data["upload_id"]
