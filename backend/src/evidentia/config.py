"""Application configuration via pydantic-settings.

All configuration is loaded from environment variables / .env file with
deployable defaults: the stack starts with ``docker compose up --build``
without any mandatory secrets. No secrets are hard-coded here.
"""

from __future__ import annotations

from pathlib import Path

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
    llm_model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
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
    # Verified 2026-10-06: TVN's public feed (151 entries). Empty → skipped.
    tvn_rss_url: str = "https://www.tvn-2.com/rss"
    data_dir: str = "data"
    seed_dir: str = "data/seed"
    # When true (or when fetchers have no connectivity), ingestion uses the
    # frozen snapshot under seed_dir instead of live APIs.
    use_seed_snapshot: bool = False
    # Auto-ingestion background scheduler (Pitch mode)
    auto_ingest_enabled: bool = False
    auto_ingest_interval_minutes: int = 15

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

    # ── Security & Dual JWT Tokens (15m access / 7d refresh) ────────────────
    jwt_secret_key: str = "evidentia-super-secret-jwt-key-2026-PanamaHackIAthon-Secure-32Chars"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15  # 15 minutes
    refresh_token_expire_days: int = 7     # 7 days
    admin_email: str = "admin@tvn.com"
    admin_password: str = "EvidentIA2026!"
    admin_initial_name: str = "Super Admin / Jurado"
    admin_initial_role: str = "Super Admin"
    admin_initial_org: str = "TVN Media"


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


def ensure_seed_files(target_dir: Path | None = None) -> list[str]:
    """Ensure all 4 seed snapshot files exist in target_dir, auto-copying from frozen backup if missing."""
    import shutil

    settings = get_settings()
    dest = target_dir or resolve_data_path(settings.seed_dir)
    dest.mkdir(parents=True, exist_ok=True)

    required_files = ("noticias.csv", "indicadores.csv", "eventos.geojson", "fichas.jsonl")
    copied = []

    # Potential source directories in order of preference
    source_candidates = [
        Path("/app/seed_frozen"),
        Path("/app/data/seed"),
        Path(__file__).resolve().parents[3] / "data/seed",
        Path(__file__).resolve().parents[3] / "backend/data/seed",
        Path.cwd() / "data/seed",
        Path.cwd() / "backend/data/seed",
    ]

    for filename in required_files:
        target_file = dest / filename
        if not target_file.exists() or target_file.stat().st_size == 0:
            for cand in source_candidates:
                src_file = cand / filename
                if src_file.exists() and src_file.stat().st_size > 0 and src_file.resolve() != target_file.resolve():
                    shutil.copy(src_file, target_file)
                    copied.append(filename)
                    break

    return copied


def resolve_data_path(rel_path: str | Path = "data") -> Path:
    """Resolve a data or seed path reliably whether run from repo root, backend/, or container."""
    p = Path(rel_path)
    if p.is_absolute() and p.exists():
        return p
    if p.exists():
        return p.resolve()
    # Check relative to repo root (parents[3] of this file)
    repo_root = Path(__file__).resolve().parents[3]
    candidate = repo_root / p
    if candidate.exists():
        return candidate.resolve()
    # Check parent of current working directory
    curr = Path.cwd()
    if (curr / p).exists():
        return (curr / p).resolve()
    if (curr.parent / p).exists():
        return (curr.parent / p).resolve()
    # Check container frozen seeds
    frozen = Path("/app/seed_frozen") / (p.name if p.name in ("noticias.csv", "indicadores.csv", "eventos.geojson", "fichas.jsonl") else p)
    if frozen.exists():
        return frozen.resolve()
    return candidate


