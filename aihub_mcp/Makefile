lint:
	@echo "Running linter for aihub_mcp..."
	poetry run ruff check --fix

format:
	@echo "Formatting code for aihub_mcp..."
	poetry run ruff format

typecheck:
	@echo "Running type checks for aihub_mcp..."
	poetry run mypy .

pr-ready: format lint
	@echo "Running full check (format, lint)..."

test-cov:
	@echo "Running tests in aihub_mcp with coverage..."
	poetry run pytest --cov=. \
	                  --cov-report=xml:coverage.xml \
	                  --cov-report=term-missing \
	                  --junitxml=pytest.xml

test:
	@echo "Running tests in aihub_mcp..."
	poetry run pytest

use-local-core:
	@echo "Switching to local aihub_lib..."
	poetry remove aihub_lib
	poetry add --editable ../aihub_lib

NUM_WORKERS = $(shell echo $${NUM_WORKERS:-$$(( $$(nproc) * 1 ))})

run-prod:
	@echo "Starting MCP server with Gunicorn using ${NUM_WORKERS} workers..."
	poetry run gunicorn -w ${NUM_WORKERS} \
		-k uvicorn.workers.UvicornWorker \
		--timeout=300 \
		-b 0.0.0.0:8001 \
		--forwarded-allow-ips=* \
		app.main:app

playground:
	@echo "Starting MCP playground..."
	poetry run python playground/server/main.py
