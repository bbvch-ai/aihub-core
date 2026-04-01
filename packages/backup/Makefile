lint:
	@echo "Running linter..."
	uv run ruff check --fix

format:
	@echo "Formatting code..."
	uv run ruff format

typecheck:
	@echo "Running type checks..."
	uv run ty check

pr-ready: format lint
	@echo "Running full check (format, lint)..."

test:
	@echo "Running tests in swiss_ai_hub.backup..."
	uv run pytest

dev:
	@echo "Starting Dagster dev server on http://localhost:3004..."
	uv run dagster dev -m swiss_ai_hub.backup.dagster -p 3004
