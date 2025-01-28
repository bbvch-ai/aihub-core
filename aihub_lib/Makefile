lint:
	@echo "Running linter for pipelines..."
	poetry run ruff check --fix

format:
	@echo "Formatting code for pipelines..."
	poetry run ruff format

typecheck:
	@echo "Running type checks for pipelines..."
	poetry run mypy .

sort-imports:
	@echo "Sorting imports for pipelines..."
	poetry run isort .

pr-ready: sort-imports format
	@echo "Running full check (format, sort)..."

test-cov:
	@echo "Running tests in aihub_lib with coverage..."
	poetry run pytest --cov=aihub_lib \
	                  --cov-report=xml:coverage.xml \
	                  --cov-report=term-missing \
	                  --junitxml=pytest.xml
