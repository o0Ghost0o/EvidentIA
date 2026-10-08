FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# System libs for OpenCV-headless/docling runtime and healthchecks.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        wget \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

# spaCy Spanish model for entity extraction (downloaded at build time so
# `docker compose up` needs no network access afterwards).
RUN uv run python -m spacy download es_core_news_sm

COPY src ./src
COPY data/seed ./data/seed

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src

ENV PORT=8000
EXPOSE ${PORT}

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || wget -qO- http://localhost:8000/health || exit 1

CMD ["sh", "-c", "uv run uvicorn evidentia.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${UVICORN_WORKERS:-2}"]
