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

test-cov:
	@echo "Running tests in swiss_ai_hub.core with coverage..."
	uv run pytest --cov=. \
	                  --cov-report=xml:coverage.xml \
	                  --cov-report=term-missing \
	                  --junitxml=pytest.xml

test:
	@echo "Running tests in swiss_ai_hub.core..."
	uv run pytest
