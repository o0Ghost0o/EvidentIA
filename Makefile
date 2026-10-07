.DEFAULT_GOAL := help

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

setup: ## Copy env template and install backend + frontend deps
	cp -n .env.example .env || true
	cd backend && uv sync
	cd frontend && npm install

dev: ## Start infra in Docker; backend/frontend run locally (see output)
	docker compose up -d postgres qdrant redis
	@echo "Infra up. In two shells:"
	@echo "  cd backend && uv run uvicorn evidentia.main:app --reload --port 8000"
	@echo "  cd frontend && npm run dev   # http://localhost:3000"

test: ## Backend test suite
	cd backend && uv run pytest

ingest: ## Live ingestion (sync) into local processed/
	cd backend && uv run python -c "from evidentia.ingestion.pipeline import run_ingestion; print(run_ingestion()['families'])"

seed: ## Rebuild the frozen snapshot in data/seed (needs internet)
	uv --project backend run python scripts/fetch_seed_data.py

benchmark: ## Build data/benchmark.jsonl from processed/seed data
	uv --project backend run python scripts/build_benchmark.py

build: ## Build all Docker images
	docker compose build

up: ## Start the full stack (app http://localhost:8080, api http://localhost:8001)
	docker compose up --build

down: ## Stop the stack
	docker compose down

notion: ## Sync docs/notion/*.md to Notion (needs NOTION_TOKEN + NOTION_PARENT_PAGE_ID)
	uv --project backend run python scripts/sync_notion.py
