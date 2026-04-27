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
	@echo "Running unit tests in swiss_ai_hub.backup..."
	uv run pytest -m unit

test-integration:
	@echo "Running integration tests in swiss_ai_hub.backup..."
	uv run pytest -m integration

test-all:
	@echo "Running all tests in swiss_ai_hub.backup..."
	uv run pytest
