"""Database engine, sessions and initialisation."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.engine import Engine

from evidentia.config import get_settings

_engine: Engine | None = None


def get_engine() -> Engine:
    """Return a cached SQLAlchemy engine built from settings."""
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
        _engine = create_engine(settings.database_url, connect_args=connect_args)
    return _engine


def reset_engine() -> None:
    """Drop the cached engine (tests only)."""
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None


def init_db() -> None:
    """Create all tables (idempotent). No migrations for the prototype scope."""
    from evidentia import models  # noqa: F401  (register tables)

    SQLModel.metadata.create_all(get_engine())


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a request-scoped session."""
    with Session(get_engine()) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
