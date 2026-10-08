"""FastAPI application factory — EvidentIA backend.

Lifespan:
  - Creates SQLModel tables (idempotent).
  - Attaches shared settings to app.state for routers.
  - Initialises Qdrant collections idempotently (retrieval).

Startup never hard-fails on a missing backing service: probes report the
degraded state and requests fail gracefully per dependency.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from evidentia.api.auth import router as auth_router
from evidentia.api.cases import router as cases_router
from evidentia.api.evidence import router as evidence_router
from evidentia.api.health import router as health_router
from evidentia.api.ingest import router as ingest_router
from evidentia.api.jurado import router as jurado_router
from evidentia.api.ranking import router as ranking_router
from evidentia.auth.dependencies import get_current_user
from evidentia.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown lifecycle."""
    settings = get_settings()
    app.state.settings = settings

    try:
        from evidentia.auth.dependencies import bootstrap_initial_admin
        from evidentia.db import get_engine, init_db
        from sqlmodel import Session

        init_db()
        with Session(get_engine()) as session:
            bootstrap_initial_admin(session)
        logger.info("Database tables and admin user initialised.")
    except Exception as exc:
        logger.error("Database initialisation failed (degraded mode): %s", exc)

    try:
        from evidentia.retrieval.store import get_qdrant_client, init_collections

        qdrant = get_qdrant_client(settings)
        init_collections(qdrant, settings)
        app.state.qdrant_client = qdrant
    except Exception as exc:
        app.state.qdrant_client = None
        logger.error("Qdrant initialisation failed (degraded mode): %s", exc)

    # Auto-bootstrap offline seed snapshot if USE_SEED_SNAPSHOT is true and database is empty
    if settings.use_seed_snapshot:
        try:
            from sqlmodel import Session, select
            from evidentia import models
            from evidentia.db import get_engine

            with Session(get_engine()) as session:
                has_news = session.exec(select(models.NewsArticle)).first() is not None

            if not has_news:
                logger.info("USE_SEED_SNAPSHOT=true and database empty: auto-bootstrapping seed snapshot...")
                from evidentia.ingestion.pipeline import run_ingestion

                run_ingestion(use_seed=True)
                logger.info("Seed snapshot auto-bootstrapped successfully.")
        except Exception as exc:
            logger.warning("Seed auto-bootstrap failed (skipping): %s", exc)

    # Start auto-ingest background scheduler
    from evidentia.ingestion.scheduler import scheduler

    scheduler.start()

    yield

    # Clean shutdown
    await scheduler.stop()


def create_app() -> FastAPI:
    app = FastAPI(
        title="EvidentIA",
        description="Copiloto de entorno y verificación trazable — hackIAthon Panamá, reto TVN Media.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(ingest_router, dependencies=[Depends(get_current_user)])
    app.include_router(ranking_router, dependencies=[Depends(get_current_user)])
    app.include_router(cases_router, dependencies=[Depends(get_current_user)])
    app.include_router(evidence_router, dependencies=[Depends(get_current_user)])
    app.include_router(jurado_router, dependencies=[Depends(get_current_user)])
    return app


app = create_app()
