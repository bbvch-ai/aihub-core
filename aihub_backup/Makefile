lint:
	@echo "Running linter..."
	uv run ruff check --fix

format:
	@echo "Formatting code..."
	uv run ruff format

typecheck:
	@echo "Running type checks..."
	uv run mypy aihub_backup

test:
	@echo "Running tests in aihub_backup..."
	uv run pytest -m "not e2e"

test-cov:
	@echo "Running tests in aihub_backup with coverage..."
	uv run pytest --cov=. \
	                  --cov-report=xml:coverage.xml \
	                  --cov-report=term-missing \
	                  --junitxml=pytest.xml

pr-ready: format lint typecheck
	@echo "Running full check (format, lint, typecheck)..."

dev:
	@echo "Starting Dagster dev server on http://localhost:3004..."
	@test -f "$(CURDIR)/../.env" || { echo "ERROR: No .env found at repo root (copy from .env.dev)"; exit 1; }
	@set -a && . "$(CURDIR)/../.env" && set +a && \
	export POSTGRES_HOST=localhost && \
	export POSTGRES_FERRETDB_HOST=localhost && \
	export MILVUS_HOST=localhost && \
	export CLICKHOUSE_HOST=localhost && \
	export VALKEY_HOST=localhost && \
	export NATS_URL=nats://localhost:4222 && \
	export AWS_ENDPOINT_URL=http://localhost:9000 && \
	uv run dagster dev -m aihub_backup.dagster -p 3004
