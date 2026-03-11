lint:
	@echo "Running linter..."
	uv run ruff check --fix

# Format code with Black
format:
	@echo "Formatting code..."
	uv run ruff format

# Type-check with ty
typecheck:
	@echo "Running type checks..."
	uv run ty check

clean-jupyter:
	@echo "Cleaning up notebooks..."
	jupyter nbconvert --ClearOutputPreprocessor.enabled=True --clear-output --inplace **/*.ipynb

test-cov:
	@echo "Running tests in swiss_ai_hub.agent with coverage..."
	uv run pytest --cov=. \
	                  --cov-report=xml:coverage.xml \
	                  --cov-report=term-missing \
	                  --junitxml=pytest.xml

test:
	@echo "Running tests in swiss_ai_hub.agent..."
	uv run pytest

pr-ready: format lint
	@echo "Running full check (format, sort)..."
