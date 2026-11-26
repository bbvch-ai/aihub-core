-include ../.env
export

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
	@echo "Running tests in swiss_ai_hub.ee with coverage..."
	uv run pytest --cov=. \
	                  --cov-report=xml:coverage.xml \
	                  --cov-report=term-missing \
	                  --junitxml=pytest.xml

test:
	@echo "Running tests in swiss_ai_hub.ee..."
	uv run pytest

pr-ready: format lint
	@echo "Running full check (format, lint)..."

run-universal-agent:
	uv run python -m app.universal_agent.main

run-email-classification-agent:
	uv run python -m app.email_classification_agent.main
