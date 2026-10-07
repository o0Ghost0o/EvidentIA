.DEFAULT_GOAL := help

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-12s %s\n", $$1, $$2}'

setup: ## Copy env template, install deps and configure git hooks
	cp -n .env.example .env || true
	cd backend && uv sync
	cd frontend && bun install || npm install
	git config core.hooksPath .githooks
	chmod +x .githooks/*

hooks: ## Configure git hooks for branch protection and Linear validation
	git config core.hooksPath .githooks
	chmod +x .githooks/*
	@echo "✓ Git hooks configured (.githooks)"

dev: ## Start infra in Docker; backend/frontend run locally (see output)
	docker compose up -d postgres qdrant redis
	@echo "Infra up. In two shells:"
	@echo "  cd backend && uv run uvicorn evidentia.main:app --reload --port 8000"
	@echo "  cd frontend && npm run dev   # http://localhost:3000"

test: ## Backend test suite
	cd backend && uv run pytest

test-e2e-preflight: ## Check DNS, SSL and HTTP health of dev endpoints
	python3 scripts/check_dev_endpoints.py

test-e2e-api: ## Run E2E API live test suite against dev-evidentia-api.vertexdc.com
	uv run --project backend pytest tests/e2e/test_api_live.py -v

test-e2e-ui: ## Run Playwright E2E UI test suite against dev-evidentia.vertexdc.com
	cd frontend && bun run test:e2e

test-e2e: ## Run full E2E suite (preflight + API + UI)
	@echo "==> Running E2E Preflight..."
	@python3 scripts/check_dev_endpoints.py || true
	@echo "==> Running E2E API Tests..."
	@uv run --project backend pytest tests/e2e/test_api_live.py -v
	@echo "==> Running E2E UI Tests (Playwright)..."
	@cd frontend && bun run test:e2e

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
