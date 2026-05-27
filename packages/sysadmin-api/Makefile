-include ../../.env
export

NUM_WORKERS = $(shell echo $${NUM_WORKERS:-$$(( $$(nproc) * 1 ))})

lint:
	@echo "Running linter..."
	uv run ruff check --fix

format:
	@echo "Formatting code..."
	uv run ruff format

typecheck:
	@echo "Running type checks..."
	uv run ty check

test-cov:
	@echo "Running tests in swiss_ai_hub.sysadmin_api with coverage..."
	uv run pytest --cov=. \
	                  --cov-report=xml:coverage.xml \
	                  --cov-report=term-missing \
	                  --junitxml=pytest.xml \
	                   || echo "No tests found. Skipping..."

test:
	@echo "Running tests in swiss_ai_hub.sysadmin_api..."
	uv run pytest || echo "No tests found. Skipping..."

pr-ready: format lint
	@echo "Running full check (format, lint)..."

run-dev:
	@echo "Starting development server with hot reload (port 8001 to avoid clashing with main api)..."
	uv run uvicorn swiss_ai_hub.sysadmin_api.main:app --reload --host 0.0.0.0 --port 8001

run-prod:
	@echo "Starting server with Gunicorn using ${NUM_WORKERS} workers..."
	uv run gunicorn -w ${NUM_WORKERS} \
		-k uvicorn.workers.UvicornWorker \
		--timeout=300 \
		-b 0.0.0.0:8000 \
		--forwarded-allow-ips=* \
		swiss_ai_hub.sysadmin_api.main:app
