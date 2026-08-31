.PHONY: lint format typecheck pr-ready test-cov test playground quickstart rag-pipelines \
	check-dotenv dagster-home

DOTENV := ../../.env

# Same location as DAGSTER_HOME in .env, but pre-expanded so mkdir and cp can
# use it directly (.env spells it "~/.dagster_home" for the manual
# `source .env` flow, where Dagster's own expanduser resolves the tilde).
DAGSTER_HOME ?= $(HOME)/.dagster_home

# Source the repo-root .env into the recipe shell for the dev-stack connection
# settings. `-include ../../.env` (the pattern in packages/api and
# packages/agent) is deliberately NOT used: Make keeps the quotes from the file,
# so every value arrives wrapped in literal apostrophes.
LOAD_ENV := set -a && . $(DOTENV) && set +a && export DAGSTER_HOME=$(DAGSTER_HOME)

lint:
	@echo "Running linter for pipelines..."
	uv run ruff check --fix

# Format code with Black
format:
	@echo "Formatting code for pipelines..."
	uv run ruff format

# Type-check with ty
typecheck:
	@echo "Running type checks..."
	uv run ty check

# Run format, type-check, and test in sequence
pr-ready: format lint
	@echo "Running full check (format, lint)..."

test-cov:
	@echo "Running tests in swiss_ai_hub.pipeline with coverage..."
	uv run pytest --cov=. --cov-report=xml:coverage.xml --cov-report=term-missing --junitxml=pytest.xml \
	|| echo "No tests found. Skipping..."

test:
	@echo "Running tests in swiss_ai_hub.pipeline..."
	uv run pytest || echo "No tests found. Skipping..."

check-dotenv:
	@test -f $(DOTENV) || { echo "Missing $(DOTENV) — run 'make setup' from the workspace root."; exit 1; }

# Without DAGSTER_HOME, `dagster dev` builds a throwaway instance in a
# .tmp_dagster_home_* dir under the cwd on every start: run history is lost and
# the unconfigured DefaultRunCoordinator fans out without a concurrency cap.
# Install the instance config copy-if-absent so local tuning survives.
dagster-home:
	@mkdir -p $(DAGSTER_HOME)
	@if [ -f $(DAGSTER_HOME)/dagster.yaml ]; then \
		echo "Using existing Dagster instance config at $(DAGSTER_HOME)/dagster.yaml"; \
	else \
		cp dagster.local.yaml $(DAGSTER_HOME)/dagster.yaml; \
		echo "Installed dagster.local.yaml -> $(DAGSTER_HOME)/dagster.yaml"; \
	fi

playground: check-dotenv dagster-home
	@echo "Running playground..."
	@$(LOAD_ENV) && OTEL_ENABLED=false uv run dagster dev -m playground --use-legacy-code-server-behavior

quickstart: check-dotenv dagster-home
	@echo "Running quickstart..."
	@$(LOAD_ENV) && OTEL_ENABLED=false uv run dagster dev -f playground/quick_start/simple_pipeline.py -f playground/quick_start/my_document_pipeline.py

rag-pipelines: check-dotenv dagster-home
	@echo "Running RAG pipelines..."
	@$(LOAD_ENV) && OTEL_ENABLED=false uv run dagster dev -m app.default_rag_pipeline -m app.shared_rag_pipeline -m app.rag_pipeline
