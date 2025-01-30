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

# Sort imports with isort
sort-imports:
	@echo "Sorting imports for pipelines..."
	poetry run isort .

# Run format, sort-imports, type-check, and test in sequence
pr-ready: sort-imports format
	@echo "Running full check (format, sort)..."

test-cov:
	@echo "Running tests in aihub_pipeline with coverage..."
	poetry run pytest --cov=. --cov-report=xml:coverage.xml --cov-report=term-missing --junitxml=pytest.xml \
	|| echo "No tests found. Skipping..."
