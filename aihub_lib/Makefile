lint:
	@echo "Running linter for pipelines..."
	poetry run ruff check --fix

format:
	@echo "Formatting code for pipelines..."
	poetry run ruff format

typecheck:
	@echo "Running type checks for pipelines..."
	poetry run mypy .

pr-ready: format lint
	@echo "Running full check (format, lint)..."

test-cov:
	@echo "Running tests in aihub_lib with coverage..."
	poetry run pytest --cov=. \
	                  --cov-report=xml:coverage.xml \
	                  --cov-report=term-missing \
	                  --junitxml=pytest.xml

test:
	@echo "Running tests in aihub_lib..."
	poetry run pytest
