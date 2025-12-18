lint:
	@echo "Running linter..."
	@(cd aihub_pipeline && make lint)
	@(cd aihub_lib && make lint)
	@(cd aihub_agent && make lint)
	@(cd aihub_process && make lint)
	@(cd aihub_api && make lint)
	@(cd aihub_bot && make lint)

# Format code with Black
format:
	@echo "Formatting code for pipelines..."
	@(cd aihub_pipeline && make format)
	@(cd aihub_lib && make format)
	@(cd aihub_agent && make format)
	@(cd aihub_process && make format)
	@(cd aihub_api && make format)
	@(cd aihub_bot && make format)

format-md:
	@echo "Formatting markdown files..."
	@poetry run mdformat --number $$(git ls-files '*.md')

format-md-win:
	@echo "Formatting markdown files..."
	@powershell -Command "git ls-files *.md | ForEach-Object { poetry run mdformat --number $$_ }"

# Type-check with MyPy
typecheck:
	@echo "Running type checks for pipelines..."
	@(cd aihub_pipeline && make typecheck)
	@(cd aihub_lib && make typecheck)
	@(cd aihub_agent && make typecheck)
	@(cd aihub_process && make typecheck)
	@(cd aihub_api && make typecheck)
	@(cd aihub_bot && make typecheck)

# Run format, type-check, and test in sequence
pr-ready:
	@echo "Running full check (format, lint)..."
	@(cd aihub_pipeline &&  make pr-ready)
	@(cd aihub_lib &&  make pr-ready)
	@(cd aihub_agent &&  make pr-ready)
	@(cd aihub_process &&  make pr-ready)
	@(cd aihub_api &&  make pr-ready)
	@(cd aihub_bot &&  make pr-ready)
	@(cd aihub_web && make pr-ready)
	@poetry run mdformat --number $$(git ls-files '*.md')

# Use local cores for development (with poetry install)
use-local-core:
	@echo "Switching to local cores with poetry install..."
	poetry run python switch_dependencies.py local --install

# Use local cores without running poetry install (for CI)
use-local-core-without-install:
	@echo "Switching to local cores without poetry install..."
	poetry run python switch_dependencies.py local

TAG ?= v0.256.3

# Use remote cores (with poetry install)
use-remote-core:
	@echo "Switching all microservices to remote with tag: $(TAG)"
	poetry run python switch_dependencies.py remote --tag "$(TAG)" --install

# Use remote cores without running poetry install (for CI)
use-remote-core-without-install:
	@echo "Switching all microservices to remote with tag: $(TAG) without poetry install..."
	poetry run python switch_dependencies.py remote --tag "$(TAG)"

changelog:
	@echo "Generating changelog"
	/bin/bash ./generate-changelog.sh
	@poetry run mdformat --number $$(git ls-files '*.md')

# Check licenses across all dependencies
license-check:
	@echo "Checking licenses..."
	/bin/bash ./generate-license.sh
	@poetry run mdformat --number $$(git ls-files '*.md')

# Generate Docker Compose files from the template
generate-compose:
	@echo "Generating Docker Compose files..."
	@poetry run python deployment/generate_compose.py

local-cert:
	@echo "Generating mkcert certificates for localhost and nip.io..."
	mkdir -p configs/traefik/certs
	mkcert -key-file configs/traefik/certs/dev-key.pem -cert-file configs/traefik/certs/dev-cert.pem \
		"localhost" "*.localhost" \
		"127.0.0.1.nip.io" "*.127.0.0.1.nip.io"
	@echo "✅ Certificates written to configs/traefik/certs/dev-cert.pem and configs/certs/dev-key.pem"

up-dev:
	@echo "Starting development environment with Docker Compose..."
	docker compose -f docker-compose.dev.yml --env-file .env up -d --build

generate-api-token:
	@echo "Generating API token..."
	cd aihub_api && poetry run python generate_api_token.py
