"""Ingestion endpoints: trigger loads and read the quality report."""

from __future__ import annotations

import json
from typing import Annotated
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile
import pydantic

from evidentia import models
from evidentia.auth.dependencies import require_role
from evidentia.config import get_settings

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/run")
def run_ingest(
    sync: bool = Query(default=False, description="Run inline instead of queueing"),
    use_seed: bool = Query(default=False, description="Load the frozen seed snapshot"),
    current_user: Annotated[models.User, Depends(require_role("Admin"))] = None,
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
def set_auto_schedule(
    body: ScheduleConfigRequest,
    current_user: Annotated[models.User, Depends(require_role("Super Admin"))] = None,
) -> dict:
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


@router.get("/templates/{family}")
def download_template(family: str) -> Response:
    """Download official sample schema template for noticias, indicadores, eventos, or fichas."""
    from evidentia.config import resolve_data_path

    fam = family.lower().replace(".csv", "").replace(".geojson", "").replace(".jsonl", "").strip()
    mapping = {
        "noticias": ("plantilla_noticias.csv", "text/csv; charset=utf-8"),
        "indicadores": ("plantilla_indicadores.csv", "text/csv; charset=utf-8"),
        "eventos": ("plantilla_eventos.geojson", "application/geo+json; charset=utf-8"),
        "fichas": ("plantilla_fichas.jsonl", "application/x-ndjson; charset=utf-8"),
    }
    if fam not in mapping:
        raise HTTPException(status_code=400, detail=f"Familia no válida: '{family}'. Opciones: noticias, indicadores, eventos, fichas.")

    filename, media_type = mapping[fam]
    template_path = resolve_data_path(Path("data/templates") / filename)
    if not template_path.exists():
        template_path = resolve_data_path(Path("backend/data/templates") / filename)
    if not template_path.exists():
        raise HTTPException(status_code=404, detail=f"Plantilla '{filename}' no encontrada.")

    content = template_path.read_bytes()
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/uploads")
def get_upload_history() -> list[dict]:
    """Return historical upload records with status, timestamp, and duplicate details."""
    from evidentia.config import get_settings, resolve_data_path

    processed_dir = resolve_data_path(Path(get_settings().data_dir) / "processed")
    history_path = processed_dir / "upload_history.json"
    if not history_path.exists():
        alt = resolve_data_path("data/processed/upload_history.json")
        if alt.exists():
            history_path = alt
    if not history_path.exists():
        return []
    try:
        return json.loads(history_path.read_text(encoding="utf-8"))
    except Exception:
        return []



@router.post("/upload")
async def upload_file(
    file: UploadFile,
    family: str | None = None,
    current_user: Annotated[models.User, Depends(require_role("Admin"))] = None,
) -> dict:
    """Upload data file, validate schema, detect duplicates, and record upload metadata."""
    import csv
    import io
    import uuid
    from datetime import datetime, timezone

    from evidentia.config import get_settings, resolve_data_path
    from evidentia.ingestion import validators
    from evidentia.ingestion.pipeline import (
        INDICATOR_FIELDS,
        NEWS_FIELDS,
        _read_csv,
        _read_geojson,
        _upsert_db,
        _write_csv,
        _write_geojson,
    )

    filename = file.filename or "upload"
    fn_lower = filename.lower()

    # Determine data family
    fam = (family or "").lower().strip()
    if not fam:
        if "noticia" in fn_lower or "news" in fn_lower:
            fam = "noticias"
        elif "indicador" in fn_lower or "indicator" in fn_lower:
            fam = "indicadores"
        elif "evento" in fn_lower or fn_lower.endswith(".geojson"):
            fam = "eventos"
        elif "ficha" in fn_lower or fn_lower.endswith(".jsonl"):
            fam = "fichas"
        else:
            raise HTTPException(
                status_code=400,
                detail="No se pudo determinar la familia de datos. Por favor especifica 'family' (noticias, indicadores, eventos, fichas).",
            )

    fam = fam.replace(".csv", "").replace(".geojson", "").replace(".jsonl", "").strip()
    if fam not in ("noticias", "indicadores", "eventos", "fichas"):
        raise HTTPException(
            status_code=400,
            detail=f"Familia '{fam}' desconocida. Debe ser: noticias, indicadores, eventos, fichas.",
        )

    # Read and decode uploaded content
    raw_bytes = await file.read()
    raw_text = raw_bytes.decode("utf-8", errors="replace")

    upload_id = f"upl-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    now_utc = datetime.now(timezone.utc).isoformat()

    settings = get_settings()
    processed_dir = resolve_data_path(Path(settings.data_dir) / "processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    total_rows = 0
    valid_rows = 0
    dropped_rows = 0
    duplicate_errors: list[dict] = []
    error_sample: list[dict] = []

    if fam == "noticias":
        try:
            reader = csv.DictReader(io.StringIO(raw_text))
            raw_data = list(reader)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Error parseando CSV de noticias: {exc}")

        total_rows = len(raw_data)
        v_res = validators.validate_news(raw_data)
        valid_rows = len(v_res.valid)
        dropped_rows = v_res.dropped
        error_sample = v_res.errors[:10]
        duplicate_errors = [e for e in v_res.errors if "duplicate" in e.get("reason", "").lower()]

        if v_res.valid:
            # Upsert into DB
            _upsert_db(v_res.valid, [], [])
            # Append / merge into processed/noticias.csv
            dest_file = processed_dir / "noticias.csv"
            existing = _read_csv(dest_file) if dest_file.exists() else []
            existing_ids = {r.get("id_noticia") for r in existing if r.get("id_noticia")}
            new_to_add = [r for r in v_res.valid if r.get("id_noticia") not in existing_ids]
            merged = existing + new_to_add
            _write_csv(dest_file, merged, NEWS_FIELDS)

            # Best-effort index
            try:
                from evidentia.retrieval import indexing
                indexing.index_news(v_res.valid)
            except Exception:
                pass

    elif fam == "indicadores":
        try:
            reader = csv.DictReader(io.StringIO(raw_text))
            raw_data = list(reader)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Error parseando CSV de indicadores: {exc}")

        total_rows = len(raw_data)
        v_res = validators.validate_indicators(raw_data)
        valid_rows = len(v_res.valid)
        dropped_rows = v_res.dropped
        error_sample = v_res.errors[:10]
        duplicate_errors = [e for e in v_res.errors if "duplicate" in e.get("reason", "").lower()]

        if v_res.valid:
            _upsert_db([], v_res.valid, [])
            dest_file = processed_dir / "indicadores.csv"
            existing = _read_csv(dest_file) if dest_file.exists() else []
            existing_keys = {(r.get("pais_iso3"), r.get("indicador_id"), str(r.get("anio"))) for r in existing}
            new_to_add = [r for r in v_res.valid if (r.get("pais_iso3"), r.get("indicador_id"), str(r.get("anio"))) not in existing_keys]
            merged = existing + new_to_add
            _write_csv(dest_file, merged, INDICATOR_FIELDS)

            try:
                from evidentia.retrieval import indexing
                indexing.index_indicators(v_res.valid)
            except Exception:
                pass

    elif fam == "eventos":
        try:
            payload = json.loads(raw_text)
            features = payload.get("features", [])
            raw_data = []
            for feat in features:
                props = feat.get("properties", {}) or {}
                coords = (feat.get("geometry", {}) or {}).get("coordinates", []) or []
                raw_data.append({
                    "id": feat.get("id"),
                    "magnitude": props.get("mag"),
                    "time": props.get("time") or None,
                    "updated": props.get("updated") or None,
                    "longitude": coords[0] if len(coords) > 0 else None,
                    "latitude": coords[1] if len(coords) > 1 else None,
                    "depth": props.get("depth"),
                    "place": props.get("place"),
                    "status": props.get("status"),
                    "url": props.get("url"),
                })
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Error parseando GeoJSON de eventos: {exc}")

        total_rows = len(raw_data)
        v_res = validators.validate_events(raw_data)
        valid_rows = len(v_res.valid)
        dropped_rows = v_res.dropped
        error_sample = v_res.errors[:10]
        duplicate_errors = [e for e in v_res.errors if "duplicate" in e.get("reason", "").lower()]

        if v_res.valid:
            _upsert_db([], [], v_res.valid)
            dest_file = processed_dir / "eventos.geojson"
            existing = _read_geojson(dest_file) if dest_file.exists() else []
            existing_ids = {r.get("id") for r in existing if r.get("id")}
            new_to_add = [r for r in v_res.valid if r.get("id") not in existing_ids]
            merged = existing + new_to_add
            _write_geojson(dest_file, merged)

    elif fam == "fichas":
        try:
            raw_data = [json.loads(line) for line in raw_text.splitlines() if line.strip()]
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Error parseando JSONL de fichas: {exc}")

        total_rows = len(raw_data)
        v_res = validators.validate_fichas(raw_data)
        valid_rows = len(v_res.valid)
        dropped_rows = v_res.dropped
        error_sample = v_res.errors[:10]
        duplicate_errors = [e for e in v_res.errors if "duplicate" in e.get("reason", "").lower()]

        if v_res.valid:
            dest_file = processed_dir / "fichas.jsonl"
            existing_lines = dest_file.read_text(encoding="utf-8").splitlines() if dest_file.exists() else []
            existing_fichas = [json.loads(line) for line in existing_lines if line.strip()]
            existing_ids = {r.get("id_caso") for r in existing_fichas if r.get("id_caso")}
            new_to_add = [r for r in v_res.valid if r.get("id_caso") not in existing_ids]
            merged = existing_fichas + new_to_add
            dest_file.write_text(
                "\n".join(json.dumps(r, ensure_ascii=False) for r in merged) + "\n",
                encoding="utf-8",
            )

    duplicates_found = len(duplicate_errors) > 0
    duplicate_count = len(duplicate_errors)

    if dropped_rows == 0 and valid_rows > 0:
        status = "completed"
    elif valid_rows > 0:
        status = "completed_with_warnings"
    else:
        status = "failed"

    record = {
        "upload_id": upload_id,
        "timestamp": now_utc,
        "filename": filename,
        "family": fam,
        "status": status,
        "total_rows": total_rows,
        "valid_rows": valid_rows,
        "dropped_rows": dropped_rows,
        "duplicates_found": duplicates_found,
        "duplicate_count": duplicate_count,
        "duplicate_details": duplicate_errors[:20],
        "warnings": [e.get("reason", str(e)) for e in error_sample],
    }

    # Save to upload history
    history_file = processed_dir / "upload_history.json"
    history: list[dict] = []
    if history_file.exists():
        try:
            history = json.loads(history_file.read_text(encoding="utf-8"))
        except Exception:
            history = []
    history.insert(0, record)
    history = history[:50]  # keep last 50
    history_file.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")

    # Post-upload: regenerate ranking inbox if new records were inserted
    if valid_rows > 0:
        try:
            from sqlmodel import Session
            from evidentia.db import get_engine
            from evidentia.scoring.ranking_service import generate_and_persist_inbox

            with Session(get_engine()) as db_session:
                generate_and_persist_inbox(db_session)
        except Exception:
            pass

    return record

