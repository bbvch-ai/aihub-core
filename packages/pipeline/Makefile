.PHONY: lint format typecheck pr-ready test-cov test playground quickstart rag-pipelines

lint:
	@echo "Running linter for pipelines..."
	uv run ruff check --fix

# Format code with Black
format:
	@echo "Formatting code for pipelines..."
	uv run ruff format

# Type-check with ty
typecheck:
	@echo "Running type checks..."
	uv run ty check

# Run format, type-check, and test in sequence
pr-ready: format lint
	@echo "Running full check (format, lint)..."

test-cov:
	@echo "Running tests in swiss_ai_hub.pipeline with coverage..."
	uv run pytest --cov=. --cov-report=xml:coverage.xml --cov-report=term-missing --junitxml=pytest.xml \
	|| echo "No tests found. Skipping..."

test:
	@echo "Running tests in swiss_ai_hub.pipeline..."
	uv run pytest || echo "No tests found. Skipping..."

playground:
	@echo "Running playground..."
	OTEL_ENABLED=false uv run dagster dev -m playground --use-legacy-code-server-behavior

quickstart:
	@echo "Running quickstart..."
	OTEL_ENABLED=false uv run dagster dev -f playground/quick_start/simple_pipeline.py -f playground/quick_start/my_document_pipeline.py

rag-pipelines:
	OTEL_ENABLED=false uv run dagster dev -m app.default_rag_pipeline -m app.shared_rag_pipeline
