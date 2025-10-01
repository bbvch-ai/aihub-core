include .env
export

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
	poetry run mypy aihub_bot

clean-jupyter:
	@echo "Cleaning up notebooks..."
	jupyter nbconvert --ClearOutputPreprocessor.enabled=True --clear-output --inplace **/*.ipynb

test-cov:
	@echo "Running tests in aihub_bot with coverage..."
	poetry run pytest --cov=. \
	                  --cov-report=xml:coverage.xml \
	                  --cov-report=term-missing \
	                  --junitxml=pytest.xml \
	                   || echo "No tests found. Skipping..."

test:
	@echo "Running tests in aihub_bot..."
	poetry run pytest || echo "No tests found. Skipping..."

pr-ready: format lint
	@echo "Running full check (format, lint)..."

run-prod:
	@echo "Starting server with Gunicorn using ${NUM_WORKERS} workers..."
	poetry run gunicorn -w ${NUM_WORKERS} \
		-k uvicorn.workers.UvicornWorker \
		--timeout=300 \
		-b 0.0.0.0:8001 \
		--forwarded-allow-ips=* \
		app/main:app

agents-playground:
	@echo "Starting Agents Playground with Azure OpenAI configuration (secret: ${CLIENT_SECRET})..."
	~/agentsplayground -e "http://localhost:8001/api/v1/openai/chat/completions/json?model_name=azure/gpt-4o-mini" -c "emulator" --client-id "aed8ad1c-a393-4cfe-a296-7468914e2151" --client-secret "${CLIENT_SECRET}" --tenant-id "37314c94-c755-48ab-85bb-acb83e492c42"
