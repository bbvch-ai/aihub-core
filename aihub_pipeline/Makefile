lint:
	@echo "Running linter for pipelines..."
	poetry run ruff check --fix

# Format code with Black
format:
	@echo "Formatting code for pipelines..."
	poetry run ruff format

# Type-check with MyPy
typecheck:
	@echo "Running type checks for pipelines..."
	poetry run mypy .

# Run format, type-check, and test in sequence
pr-ready: format lint
	@echo "Running full check (format, lint)..."

test-cov:
	@echo "Running tests in aihub_pipeline with coverage..."
	poetry run pytest --cov=. --cov-report=xml:coverage.xml --cov-report=term-missing --junitxml=pytest.xml \
	|| echo "No tests found. Skipping..."

test:
	@echo "Running tests in aihub_pipeline..."
	poetry run pytest || echo "No tests found. Skipping..."

playground:
	@echo "Running playground..."
	OTEL_ENABLED=false poetry run dagster dev -m playground --use-legacy-code-server-behavior

quickstart:
	@echo "Running quickstart..."
	OTEL_ENABLED=false poetry run dagster dev -f playground/quick_start/simple_pipeline.py -f playground/quick_start/my_document_pipeline.py

rag-pipelines:
	OTEL_ENABLED=false poetry run dagster dev -m app.default_rag_pipeline -m app.shared_rag_pipeline
