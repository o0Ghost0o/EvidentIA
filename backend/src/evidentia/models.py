"""SQLModel entities — structured source of truth.

Mirrors the data contract from the challenge (noticias.csv, indicadores.csv,
eventos.geojson, fichas.jsonl, manifest.json) plus the relational layer for the
light GraphRAG (entities + typed relations) and the case workspace.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json_column() -> Column:
    """JSONB on PostgreSQL, plain JSON elsewhere (e.g. sqlite-based tests)."""
    return Column(JSON().with_variant(JSONB(), "postgresql"))


class NewsArticle(SQLModel, table=True):
    """A news record: TVN RSS metadata or GDELT DOC 2.0 hit."""

    __tablename__ = "news_articles"

    id: Optional[int] = Field(default=None, primary_key=True)
    id_noticia: str = Field(unique=True, index=True, max_length=128)
    titulo: str
    url: str = Field(unique=True, index=True)
    medio: str = Field(index=True)
    idioma: str = Field(default="es", max_length=8)
    fecha_publicacion: Optional[datetime] = Field(default=None, index=True)
    fecha_deteccion: Optional[datetime] = None
    fecha_extraccion: datetime = Field(default_factory=_utcnow)
    tema: Optional[str] = Field(default=None, index=True)
    origen: str = Field(default="gdelt", max_length=32)  # tvn | gdelt | seed
    alcance_texto: str = Field(default="titular", max_length=32)  # titular | extracto | completo
    # Provenance: primary wire agency when the piece replicates one (EFE, Reuters, …).
    agencia_primaria: Optional[str] = Field(default=None, index=True)
    # Event grouping: articles about the same event share a group id.
    grupo_evento_id: Optional[str] = Field(default=None, index=True)


class Indicator(SQLModel, table=True):
    """A World Bank indicator observation (nullable value kept explicit)."""

    __tablename__ = "indicators"

    id: Optional[int] = Field(default=None, primary_key=True)
    pais_iso3: str = Field(index=True, max_length=3)
    indicador_id: str = Field(index=True, max_length=32)
    anio: int = Field(index=True)
    valor: Optional[float] = None
    unidad: Optional[str] = Field(default=None, max_length=64)
    fuente_url: Optional[str] = None
    fecha_extraccion: datetime = Field(default_factory=_utcnow)
    licencia: str = Field(default="CC BY 4.0", max_length=64)


class GeoEvent(SQLModel, table=True):
    """A USGS seismic event (facts about quakes only)."""

    __tablename__ = "geo_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    event_id: str = Field(unique=True, index=True, max_length=64)
    magnitude: Optional[float] = None
    time: Optional[datetime] = Field(default=None, index=True)
    updated: Optional[datetime] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    depth: Optional[float] = None
    place: Optional[str] = None
    status: Optional[str] = Field(default=None, max_length=32)
    url: Optional[str] = None


class Entity(SQLModel, table=True):
    """A named entity extracted from news/indicators (graph node)."""

    __tablename__ = "entities"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True)
    tipo: str = Field(index=True, max_length=32)  # ORG | LOC | PERSON | TOPIC | …
    normalizado: str = Field(unique=True, index=True)


class Relation(SQLModel, table=True):
    """A typed edge between graph nodes.

    Node references are (tipo, id) pairs where tipo is one of
    news | indicator | event | entity and id is the row id (or natural key for
    cross-store links, stored as text).
    """

    __tablename__ = "relations"

    id: Optional[int] = Field(default=None, primary_key=True)
    origen_tipo: str = Field(index=True, max_length=16)
    origen_id: str = Field(index=True, max_length=128)
    destino_tipo: str = Field(index=True, max_length=16)
    destino_id: str = Field(index=True, max_length=128)
    # mentions | same_event | source_of | contradicts | corroborates
    tipo: str = Field(index=True, max_length=16)
    peso: float = Field(default=1.0)
    extra: dict[str, Any] = Field(default_factory=dict, sa_column=_json_column())


class Case(SQLModel, table=True):
    """A research/evaluation project (workspace unit)."""

    __tablename__ = "cases"

    id: Optional[int] = Field(default=None, primary_key=True)
    titulo: str
    modalidad: str = Field(default="tvn", max_length=16)  # tvn | banca
    queries: list[str] = Field(default_factory=list, sa_column=_json_column())
    # nuevo | en_revision | requiere_evidencia | aprobado_borrador | descartado
    estado: str = Field(default="nuevo", index=True, max_length=32)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)


class EvidenceItem(SQLModel, table=True):
    """A source linked to a case as evidence (manual or automatic)."""

    __tablename__ = "evidence_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="cases.id", index=True)
    fuente_tipo: str = Field(max_length=16)  # news | indicator | event
    fuente_id: str = Field(max_length=128)
    rol: str = Field(default="respaldo", max_length=32)  # respaldo | contradiccion | contexto
    nota: Optional[str] = None
    marcado_manual: bool = Field(default=False)


class VerificationNote(SQLModel, table=True):
    """Human review trail for a case."""

    __tablename__ = "verification_notes"

    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="cases.id", index=True)
    autor: str = Field(max_length=128)
    estado_revision: str = Field(max_length=32)
    texto: str
    created_at: datetime = Field(default_factory=_utcnow)
