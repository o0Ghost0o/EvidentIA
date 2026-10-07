"""Ingestion endpoints: trigger loads and read the quality report."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
import pydantic

from evidentia.config import get_settings

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/run")
def run_ingest(
    sync: bool = Query(default=False, description="Run inline instead of queueing"),
    use_seed: bool = Query(default=False, description="Load the frozen seed snapshot"),
) -> dict:
    """Trigger an ingestion (queued on Dramatiq by default)."""
    settings = get_settings()
    use_seed = use_seed or settings.use_seed_snapshot
    if sync:
        from evidentia.ingestion.pipeline import run_ingestion

        report = run_ingestion(use_seed=use_seed)
        return {"status": "done", "report": report}

    from evidentia.ingestion.dramatiq_actors import run_ingestion_job

    message = run_ingestion_job.send(use_seed)
    return {"status": "queued", "message_id": message.message_id, "use_seed": use_seed}


@router.get("/quality-report")
def quality_report() -> dict:
    """Return the last persisted quality report."""
    path = Path(get_settings().data_dir) / "processed" / "quality_report.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No ingestion has run yet")
    return json.loads(path.read_text(encoding="utf-8"))


class ScheduleConfigRequest(pydantic.BaseModel):
    enabled: bool | None = None
    interval_minutes: int | None = None


@router.get("/auto-schedule")
def get_auto_schedule() -> dict:
    """Return the current status of the auto-ingestion scheduler."""
    from evidentia.ingestion.scheduler import scheduler

    return scheduler.get_status()


@router.post("/auto-schedule")
def set_auto_schedule(body: ScheduleConfigRequest) -> dict:
    """Update scheduler feature flag and interval in runtime."""
    from evidentia.ingestion.scheduler import scheduler

    return scheduler.configure(
        enabled=body.enabled,
        interval_minutes=body.interval_minutes,
    )


@router.post("/live-now")
async def run_live_now() -> dict:
    """Immediately trigger live news ingestion asynchronously."""
    from evidentia.ingestion.scheduler import scheduler

    result = await scheduler.run_now(use_seed=False)
    return result
