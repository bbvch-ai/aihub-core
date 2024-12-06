lint:
	@echo "Running linter..."
	poetry run ruff check --fix

# Format code with Black
format:
	@echo "Formatting code..."
	poetry run ruff format

# Type-check with MyPy
typecheck:
	@echo "Running type checks..."
	poetry run mypy agents_core

# Sort imports with isort
sort-imports:
	@echo "Sorting imports..."
	poetry run isort agents_core

clean-jupyter:
	@echo "Cleaning up notebooks..."
	jupyter nbconvert --ClearOutputPreprocessor.enabled=True --clear-output --inplace **/*.ipynb

# Clean up unnecessary files
clean:
	@echo "Cleaning up..."
	find . -type f -name "**/*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -f coverage.xml
	rm -f .coverage
	poetry run