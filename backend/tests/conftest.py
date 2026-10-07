"""Shared fixtures: isolated settings/engine per test."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _isolated_settings(tmp_path, monkeypatch):
    """Point settings at tmp dirs + file sqlite, reset caches around each test."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("SEED_DIR", str(tmp_path / "seed"))

    from evidentia.config import reset_settings
    from evidentia.db import reset_engine

    reset_settings()
    reset_engine()
    yield
    reset_settings()
    reset_engine()
