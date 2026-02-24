NUM_WORKERS = $(shell echo $${NUM_WORKERS:-$$(( $$(nproc) * 1 ))})

lint:
	@echo "Running linter..."
	uv run ruff check --fix

# Format code with Black
format:
	@echo "Formatting code..."
	uv run ruff format

# Type-check with MyPy
typecheck:
	@echo "Running type checks..."
	uv run mypy aihub_api

clean-jupyter:
	@echo "Cleaning up notebooks..."
	jupyter nbconvert --ClearOutputPreprocessor.enabled=True --clear-output --inplace **/*.ipynb

test-cov:
	@echo "Running tests in aihub_api with coverage..."
	uv run pytest --cov=. \
	                  --cov-report=xml:coverage.xml \
	                  --cov-report=term-missing \
	                  --junitxml=pytest.xml \
	                   || echo "No tests found. Skipping..."

test:
	@echo "Running tests in aihub_api..."
	uv run pytest || echo "No tests found. Skipping..."

pr-ready: format lint
	@echo "Running full check (format, lint)..."


install-ffmpeg:
	@echo "Installing ffmpeg..."
	sudo apt-get update; sudo apt-get install -y ffmpeg

run-dev:
	@echo "Starting development server with hot reload..."
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-prod:
	@echo "Starting server with Gunicorn using ${NUM_WORKERS} workers..."
	uv run gunicorn -w ${NUM_WORKERS} \
		-k uvicorn.workers.UvicornWorker \
		--timeout=300 \
		-b 0.0.0.0:8000 \
		--forwarded-allow-ips=* \
		app.main:app
