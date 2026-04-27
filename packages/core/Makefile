lint:
	@echo "Running linter for pipelines..."
	uv run ruff check --fix

format:
	@echo "Formatting code for pipelines..."
	uv run ruff format

typecheck:
	@echo "Running type checks..."
	uv run ty check

pr-ready: format lint
	@echo "Running full check (format, lint)..."

test:
	@echo "Running unit tests in swiss_ai_hub.core..."
	uv run pytest -m unit

test-integration:
	@echo "Running integration tests in swiss_ai_hub.core..."
	uv run pytest -m integration

test-all:
	@echo "Running all tests in swiss_ai_hub.core..."
	uv run pytest

test-cov:
	@echo "Running unit tests in swiss_ai_hub.core with coverage..."
	uv run pytest -m unit --cov=. \
	                  --cov-report=xml:coverage.xml \
	                  --cov-report=term-missing \
	                  --junitxml=pytest.xml
