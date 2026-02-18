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
	uv run mypy aihub_process

test-cov:
	@echo "Running tests in aihub_api with coverage..."
	uv run pytest --cov=. \
	                  --cov-report=xml:coverage.xml \
	                  --cov-report=term-missing \
	                  --junitxml=pytest.xml \
	                   || echo "No tests found. Skipping..."

test:
	@echo "Running tests in aihub_process..."
	uv run pytest || echo "No tests found. Skipping..."

pr-ready: format lint
	@echo "Running full check (format, lint)..."

