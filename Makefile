.PHONY: help install sync format lint typecheck check test test-unit test-contract test-integration test-e2e \
	run worker dev docker-build docker-up docker-down migrate revision seed clean workflow-check

PYTHON ?= python3
PDM ?= pdm

help:
	@echo "scoring-service — developer commands"
	@echo ""
	@echo "  make install          Install PDM and project dependencies (dev + test + lint)"
	@echo "  make sync             pdm sync (respects lockfile)"
	@echo "  make format           Ruff format"
	@echo "  make lint             Ruff check"
	@echo "  make typecheck        mypy on app/"
	@echo "  make check            lint + typecheck + test (CI parity)"
	@echo "  make workflow-check   actionlint on .github/workflows (optional)"
	@echo "  make test             All pytest suites"
	@echo "  make test-unit        Unit tests only"
	@echo "  make test-contract    Contract tests"
	@echo "  make test-integration Integration tests"
	@echo "  make test-e2e         End-to-end tests"
	@echo "  make run              Run API (uvicorn)"
	@echo "  make worker           Run scoring worker"
	@echo "  make dev              API with reload (requires local Postgres or docker-up)"
	@echo "  make docker-build     Build API and worker images"
	@echo "  make docker-up        docker compose up -d"
	@echo "  make docker-down      docker compose down"
	@echo "  make migrate          alembic upgrade head"
	@echo "  make revision         Create new migration (msg=...)"
	@echo "  make seed             Seed dev data"
	@echo "  make clean            Remove caches and build artifacts"

install:
	$(PDM) install -G dev -G test -G lint

sync:
	$(PDM) sync -G dev -G test -G lint

format:
	$(PDM) run ruff format app tests
	$(PDM) run ruff check --fix app tests

lint:
	$(PDM) run ruff check app tests

typecheck:
	$(PDM) run mypy app

check: lint typecheck test
	@echo "All checks passed."

workflow-check:
	@command -v actionlint >/dev/null 2>&1 && actionlint .github/workflows/*.yml || \
		(echo "Install actionlint: https://github.com/rhysd/actionlint#installation" && exit 1)

test:
	$(PDM) run pytest tests/ -v --cov=app --cov-report=term-missing

test-unit:
	$(PDM) run pytest tests/unit -v -m unit

test-contract:
	$(PDM) run pytest tests/contract -v -m contract

test-integration:
	$(PDM) run pytest tests/integration -v -m integration

test-e2e:
	$(PDM) run pytest tests/e2e -v -m e2e

run:
	$(PDM) run uvicorn app.main:app --host $${APP_HOST:-0.0.0.0} --port $${APP_PORT:-8000}

worker:
	$(PDM) run python -m app.workers.scoring_worker

dev:
	$(PDM) run uvicorn app.main:app --reload --host $${APP_HOST:-0.0.0.0} --port $${APP_PORT:-8000}

docker-build:
	docker compose -f docker-compose.yml build

docker-up:
	docker compose -f docker-compose.yml up -d

docker-down:
	docker compose -f docker-compose.yml down

migrate:
	$(PDM) run alembic upgrade head

revision:
	@test -n "$(msg)" || (echo "Usage: make revision msg=\"your message\"" && exit 1)
	$(PDM) run alembic revision --autogenerate -m "$(msg)"

seed:
	$(PDM) run python scripts/seed_dev_data.py

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
