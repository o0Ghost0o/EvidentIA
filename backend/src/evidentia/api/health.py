"""Liveness and readiness probes."""

from __future__ import annotations

from fastapi import APIRouter

from evidentia import __version__

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness: the process is up. No dependency checks."""
    return {"status": "ok", "service": "evidentia", "version": __version__}


@router.get("/ready")
def ready() -> dict[str, object]:
    """Readiness: best-effort checks against backing services.

    Never raises: each dependency reports ok/down independently so the
    endpoint itself stays usable as a diagnostics probe.
    """
    from evidentia.config import get_settings

    settings = get_settings()
    checks: dict[str, str] = {}

    # PostgreSQL
    try:
        from sqlalchemy import text

        from evidentia.db import get_engine

        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception:
        checks["postgres"] = "down"

    # Qdrant
    try:
        import httpx

        resp = httpx.get(f"{settings.qdrant_url.rstrip('/')}/readyz", timeout=3.0)
        checks["qdrant"] = "ok" if resp.status_code == 200 else "down"
    except Exception:
        checks["qdrant"] = "down"

    # Redis
    try:
        import redis

        client = redis.Redis.from_url(settings.redis_url, socket_timeout=3)
        client.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "down"

    overall = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": overall, "checks": checks}
