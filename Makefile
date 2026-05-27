# Ensure pnpm is on PATH for non-interactive shells (e.g. make)
export PATH := $(HOME)/.local/share/pnpm:$(PATH)

setup:
	@echo "Installing all Python dependencies..."
	uv sync --all-packages
	@if [ ! -f .env ]; then \
		echo "Copying .env.dev to .env..."; \
		cp .env.dev .env; \
	else \
		echo ".env already exists, skipping copy."; \
	fi
	@echo "Setup complete! Run 'make up-dev' to start the Docker stack."

setup-frontend:
	@echo "Installing frontend dependencies..."
	pnpm install --filter @swiss-ai-hub/web... --filter @swiss-ai-hub/sysadmin-web...

setup-all: setup setup-frontend

test:
	@echo "Running tests..."
	@(cd packages/pipeline && make test)
	@(cd packages/core && make test)
	@(cd packages/agent && make test)
	@(cd packages/process && make test)
	@(cd packages/api && make test)
	@(cd packages/sysadmin-api && make test)
	@(cd packages/bot && make test)
	@(cd packages/backup && make test)
	@$(MAKE) check-env

# Verify .env.prod is consistent with the rendered docker-compose files and
# every Pydantic settings class. Fails on orphans, missing compose-required
# vars, and missing app-required vars not supplied by compose.
check-env:
	@echo "Checking env consistency (.env.prod vs rendered compose)..."
	@uv run python infra/deployment/generate_compose.py --check-env --strict-env-check

lint:
	@echo "Running linter..."
	@(cd packages/pipeline && make lint)
	@(cd packages/core && make lint)
	@(cd packages/agent && make lint)
	@(cd packages/process && make lint)
	@(cd packages/api && make lint)
	@(cd packages/sysadmin-api && make lint)
	@(cd packages/bot && make lint)
	@(cd packages/backup && make lint)

# Format code with Black
format:
	@echo "Formatting code for pipelines..."
	@(cd packages/pipeline && make format)
	@(cd packages/core && make format)
	@(cd packages/agent && make format)
	@(cd packages/process && make format)
	@(cd packages/api && make format)
	@(cd packages/sysadmin-api && make format)
	@(cd packages/bot && make format)
	@(cd packages/backup && make format)

format-md:
	@echo "Formatting markdown files..."
	@uv run mdformat --number $$(git ls-files '*.md' | grep -v 'docs/whitepaper/chapters/')

format-yaml:
	@echo "Formatting YAML files..."
	@uv run yamlfix $$(git ls-files '*.yaml' '*.yml' | grep -v 'pnpm-lock.yaml')

format-md-win:
	@echo "Formatting markdown files..."
	@powershell -Command "git ls-files *.md | ForEach-Object { uv run mdformat --number $$_ }"

# Type-check with MyPy
typecheck:
	@echo "Running type checks for pipelines..."
	@(cd packages/pipeline && make typecheck)
	@(cd packages/core && make typecheck)
	@(cd packages/agent && make typecheck)
	@(cd packages/process && make typecheck)
	@(cd packages/api && make typecheck)
	@(cd packages/sysadmin-api && make typecheck)
	@(cd packages/bot && make typecheck)

# Run format, type-check, and test in sequence
pr-ready:
	@echo "Running full check (format, lint)..."
	@(cd packages/pipeline &&  make pr-ready)
	@(cd packages/core &&  make pr-ready)
	@(cd packages/agent &&  make pr-ready)
	@(cd packages/process &&  make pr-ready)
	@(cd packages/api &&  make pr-ready)
	@(cd packages/sysadmin-api &&  make pr-ready)
	@(cd packages/bot &&  make pr-ready)
	@(cd packages/backup &&  make pr-ready)
	@(cd packages/web && make pr-ready)
	@(cd packages/sysadmin-web && make pr-ready)
	@$(MAKE) generate-compose
	@$(MAKE) check-env
	@$(MAKE) generate-env-docs
	@$(MAKE) license-check
	@$(MAKE) format-md
	@$(MAKE) format-yaml

TAG ?= v0.290.1

changelog:
	@echo "Generating changelog"
	/bin/bash ./generate-changelog.sh
	@uv run mdformat --number $$(git ls-files '*.md' | grep -v 'docs/whitepaper/chapters/')

# Extract release notes for a specific version from CHANGELOG.md (TAG=v0.267.1, OUTPUT=release-notes.md)
OUTPUT ?= release-notes.md
extract-release-notes:
	@if ! echo "$(TAG)" | grep -qE '^v[0-9]+\.[0-9]+\.[0-9]+$$'; then \
		echo "ERROR: Invalid TAG format '$(TAG)'. Expected vMAJOR.MINOR.PATCH (e.g. v0.267.1)"; \
		exit 1; \
	fi
	@awk -v ver="$(TAG)" 'index($$0, "## [" ver "]") == 1 {found=1; next} found && /^## \[/{exit} found{print}' CHANGELOG.md | sed '/^_\{3,\}/d' > $(OUTPUT)
	@if [ ! -s $(OUTPUT) ]; then \
		echo "No changelog section found for $(TAG), using fallback"; \
		echo "Release $(TAG)" > $(OUTPUT); \
	fi
	@echo "Release notes for $(TAG) written to $(OUTPUT) ($$(wc -c < $(OUTPUT)) bytes)"

# Check licenses across all dependencies
license-check:
	@echo "Checking licenses..."
	/bin/bash ./generate-license.sh
	@uv run mdformat --number $$(git ls-files '*.md' | grep -v 'docs/whitepaper/chapters/')

# Generate Docker Compose files from the template
generate-compose:
	@echo "Generating Docker Compose files..."
	@uv run python infra/deployment/generate_compose.py
	@$(MAKE) format-yaml

# Generate release bundles with version-pinned images (TAG=v0.266.0, OUTPUT_DIR=dist/release)
OUTPUT_DIR ?= dist/release
generate-release:
	@echo "Generating release bundles for $(TAG)..."
	@uv run python infra/deployment/generate_compose.py --release --tag "$(TAG)" --output-dir "$(OUTPUT_DIR)"

# Generate the environment-variables reference page in docs/
generate-env-docs:
	@echo "Generating environment-variables reference page..."
	@uv run python infra/deployment/generate_compose.py --write-env-docs

local-cert:
	@echo "Generating mkcert certificates for localhost and nip.io..."
	mkdir -p infra/configs/traefik/certs
	mkcert -key-file infra/configs/traefik/certs/dev-key.pem -cert-file infra/configs/traefik/certs/dev-cert.pem \
		"localhost" "*.localhost" \
		"127.0.0.1.nip.io" "*.127.0.0.1.nip.io"
	@echo "Certificates written to infra/configs/traefik/certs/"

install-ffmpeg:
	@echo "Installing ffmpeg..."
	sudo apt-get update; sudo apt-get install -y ffmpeg

up-dev:
	@echo "Starting development environment with Docker Compose..."
	docker compose -f infra/docker-compose.dev.yml --env-file .env up -d --build

down-dev:
	@echo "Stopping development environment..."
	docker compose -f infra/docker-compose.dev.yml --env-file .env down

# Run the Dagster playground (pipeline SDK demo) against the dev stack.
# Requires `make up-dev` first. UI at http://localhost:3000.
playground:
	@echo "Starting Dagster playground at http://localhost:3000 ..."
	cd packages/pipeline && uv run dagster dev -m playground

up-dev-gpu:
	@echo "Starting development GPU environment with Docker Compose..."
	docker compose -f infra/docker-compose.dev.gpu.yml --env-file .env up -d --build

up-build: local-cert
	@echo "Starting build environment with Docker Compose..."
	docker compose -f infra/docker-compose.build.yml --env-file .env up -d --build

up-build-gpu: local-cert
	@echo "Starting build GPU environment with Docker Compose..."
	docker compose -f infra/docker-compose.build.gpu.yml --env-file .env up -d --build

up-local: local-cert
	@echo "Starting local environment with Docker Compose..."
	docker compose -f infra/docker-compose.local.yml --env-file .env up -d

up-local-gpu: local-cert
	@echo "Starting local GPU environment with Docker Compose..."
	docker compose -f infra/docker-compose.local.gpu.yml --env-file .env up -d

# Bump version across all packages (VERSION=0.264.0)
VERSION ?= 0.263.0
version-bump:
	@echo "Bumping version to $(VERSION) across all packages..."
	@for f in pyproject.toml packages/core/pyproject.toml packages/agent/pyproject.toml packages/api/pyproject.toml packages/sysadmin-api/pyproject.toml packages/bot/pyproject.toml packages/pipeline/pyproject.toml packages/process/pyproject.toml packages/backup/pyproject.toml; do \
		sed -i '/^\[project\]/,/^version =/ s/version = "[^"]*"/version = "$(VERSION)"/' $$f; \
	done
	@sed -i 's/"version": "[^"]*"/"version": "$(VERSION)"/' packages/web/package.json
	@sed -i 's/"version": "[^"]*"/"version": "$(VERSION)"/' packages/sysadmin-web/package.json
	@sed -i 's/^TAG ?= .*/TAG ?= v$(VERSION)/' Makefile
	@uv lock
	@echo "Version bumped to $(VERSION)"

