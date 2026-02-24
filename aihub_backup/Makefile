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
	uv run pytest

test-cov:
	@echo "Running tests in aihub_backup with coverage..."
	uv run pytest --cov=. \
	                  --cov-report=xml:coverage.xml \
	                  --cov-report=term-missing \
	                  --junitxml=pytest.xml

pr-ready: format lint typecheck
	@echo "Running full check (format, lint, typecheck)..."

dev:
	@echo "Starting Dagster dev server..."
	uv run dagster dev -m aihub_backup.dagster
