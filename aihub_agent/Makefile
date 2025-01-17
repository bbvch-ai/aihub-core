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
	poetry run mypy aihub_agent

# Sort imports with isort
sort-imports:
	@echo "Sorting imports..."
	poetry run isort aihub_agent

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

test-cov:
	@echo "Running tests in aihub_agent with coverage..."
	poetry run pytest --cov=aihub_agent \
	                  --cov-report=xml:coverage.xml \
	                  --cov-report=term-missing \
	                  --junitxml=pytest.xml \
	                  --ignore=playground/agent/RAGAgent/tests

pr-ready: sort-imports format
	@echo "Running full check (format, sort)..."