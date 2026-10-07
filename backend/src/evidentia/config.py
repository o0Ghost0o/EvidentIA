"""Application configuration via pydantic-settings.

All configuration is loaded from environment variables / .env file with
deployable defaults: the stack starts with ``docker compose up --build``
without any mandatory secrets. No secrets are hard-coded here.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Models (Together.ai, OpenAI-compatible) ──────────────────────────────
    # Empty key → generation endpoints answer with a structured abstention and
    # the rest of the system keeps working on the local snapshot.
    together_api_key: str = ""
    together_base_url: str = "https://api.together.xyz/v1"
    llm_model: str = "zai-org/GLM-5.3"
    # Local embedding model (fastembed/ONNX, no API key required)
    embedding_model: str = "BAAI/bge-base-en-v1.5"
    embedding_dimensions: int = 768

    # ── PostgreSQL (structured source of truth) ──────────────────────────────
    # Compose overrides with the postgres service hostname.
    database_url: str = "postgresql+psycopg://evidentia:evidentia@localhost:5432/evidentia"

    # ── Qdrant ───────────────────────────────────────────────────────────────
    qdrant_url: str = "http://localhost:6333"
    # Dual-index collections: news (index A) and indicators (index B),
    # each with a children collection + parent docstore.
    qdrant_news_children_collection: str = "evidentia_news_children"
    qdrant_news_parents_collection: str = "evidentia_news_parents"
    qdrant_indicator_children_collection: str = "evidentia_indicator_children"
    qdrant_indicator_parents_collection: str = "evidentia_indicator_parents"

    # Search params
    qdrant_search_ef: int = 128
    retrieval_top_k: int = 8

    # ── Redis / Dramatiq ─────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Data / snapshot ──────────────────────────────────────────────────────
    tvn_rss_url: str = ""  # empty → TVN fetcher skipped (recorded in report)
    data_dir: str = "data"
    seed_dir: str = "data/seed"
    # When true (or when fetchers have no connectivity), ingestion uses the
    # frozen snapshot under seed_dir instead of live APIs.
    use_seed_snapshot: bool = False

    # ── Ingestion chunking ───────────────────────────────────────────────────
    ingestion_chunk_size: int = 1000  # chars for child text chunks
    ingestion_chunk_overlap: int = 200
    ingestion_parent_size: int = 4000  # chars for parent text passages

    # ── Scoring rules (versioned, see scoring/score.py) ──────────────────────
    scoring_rules_version: str = "v1"
    score_weight_relevance: float = 30.0
    score_weight_impact: float = 25.0
    score_weight_urgency: float = 20.0
    score_weight_novelty: float = 15.0
    score_weight_evidence: float = 10.0

    # ── Notion sync (optional; see scripts/sync_notion.py) ───────────────────
    notion_token: str = ""
    notion_parent_page_id: str = ""


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return a cached Settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Drop the cached Settings (tests only)."""
    global _settings
    _settings = None
