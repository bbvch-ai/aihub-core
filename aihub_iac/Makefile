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

pr-ready: sort-imports format lint
	@echo "Running full check (format, sort)..."