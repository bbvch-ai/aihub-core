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
	cd aihub_web/aihub_web && pnpm install

setup-all: setup setup-frontend

test:
	@echo "Running tests..."
	@(cd aihub_pipeline && make test)
	@(cd aihub_lib && make test)
	@(cd aihub_agent && make test)
	@(cd aihub_process && make test)
	@(cd aihub_api && make test)
	@(cd aihub_bot && make test)

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
	@uv run mdformat --number $$(git ls-files '*.md' | grep -v 'aihub_doc/whitepaper/chapters/')

format-yaml:
	@echo "Formatting YAML files..."
	@uv run yamlfix $$(git ls-files '*.yaml' '*.yml' | grep -v 'pnpm-lock.yaml')

format-md-win:
	@echo "Formatting markdown files..."
	@powershell -Command "git ls-files *.md | ForEach-Object { uv run mdformat --number $$_ }"

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
	@$(MAKE) generate-compose
	@$(MAKE) license-check
	@$(MAKE) format-md
	@$(MAKE) format-yaml

TAG ?= v0.267.4

changelog:
	@echo "Generating changelog"
	/bin/bash ./generate-changelog.sh
	@uv run mdformat --number $$(git ls-files '*.md' | grep -v 'aihub_doc/whitepaper/chapters/')

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
	@uv run mdformat --number $$(git ls-files '*.md' | grep -v 'aihub_doc/whitepaper/chapters/')

# Generate Docker Compose files from the template
generate-compose:
	@echo "Generating Docker Compose files..."
	@uv run python deployment/generate_compose.py

# Generate release bundles with version-pinned images (TAG=v0.266.0, OUTPUT_DIR=dist/release)
OUTPUT_DIR ?= dist/release
generate-release:
	@echo "Generating release bundles for $(TAG)..."
	@uv run python deployment/generate_compose.py --release --tag "$(TAG)" --output-dir "$(OUTPUT_DIR)"

local-cert:
	@echo "Generating mkcert certificates for localhost and nip.io..."
	mkdir -p configs/traefik/certs
	mkcert -key-file configs/traefik/certs/dev-key.pem -cert-file configs/traefik/certs/dev-cert.pem \
		"localhost" "*.localhost" \
		"127.0.0.1.nip.io" "*.127.0.0.1.nip.io"
	@echo "Certificates written to configs/traefik/certs/dev-cert.pem and configs/certs/dev-key.pem"

up-dev:
	@echo "Starting development environment with Docker Compose..."
	docker compose -f docker-compose.dev.yml --env-file .env up -d --build

# Bump version across all packages (VERSION=0.264.0)
VERSION ?= 0.263.0
version-bump:
	@echo "Bumping version to $(VERSION) across all packages..."
	@for f in aihub_lib/pyproject.toml aihub_agent/pyproject.toml aihub_api/pyproject.toml aihub_bot/pyproject.toml aihub_pipeline/pyproject.toml aihub_process/pyproject.toml; do \
		sed -i 's/^version = "[^"]*"/version = "$(VERSION)"/' $$f; \
	done
	@uv lock
	@echo "Version bumped to $(VERSION)"

