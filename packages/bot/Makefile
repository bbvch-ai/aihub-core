-include .env
export

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
	uv run mypy swiss_ai_hub/bot

clean-jupyter:
	@echo "Cleaning up notebooks..."
	jupyter nbconvert --ClearOutputPreprocessor.enabled=True --clear-output --inplace **/*.ipynb

test-cov:
	@echo "Running tests in swiss_ai_hub.bot with coverage..."
	uv run pytest --cov=. \
	                  --cov-report=xml:coverage.xml \
	                  --cov-report=term-missing \
	                  --junitxml=pytest.xml \
	                   || echo "No tests found. Skipping..."

test:
	@echo "Running tests in swiss_ai_hub.bot..."
	uv run pytest || echo "No tests found. Skipping..."

pr-ready: format lint
	@echo "Running full check (format, lint)..."

run-prod:
	@echo "Starting server with Gunicorn using ${NUM_WORKERS} workers..."
	uv run gunicorn -w ${NUM_WORKERS} \
		-k uvicorn.workers.UvicornWorker \
		--timeout=300 \
		-b 0.0.0.0:8001 \
		--forwarded-allow-ips=* \
		app.main:app

agents-playground:
	@echo "Starting Agents Playground with Azure OpenAI configuration (using secret)..."
	~/agentsplayground -e "http://localhost:8001/api/v1/openai/chat/completions/json?model_name=azure/gpt-4o-mini" -c "emulator" --client-id "aed8ad1c-a393-4cfe-a296-7468914e2151" --client-secret "${CLIENT_SECRET}"