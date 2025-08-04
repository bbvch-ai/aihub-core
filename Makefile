lint:
	@echo "Running linter..."
	@(cd aihub_pipeline && make lint)
	@(cd aihub_lib && make lint)
	@(cd aihub_agent && make lint)
	@(cd aihub_process && make lint)
	@(cd aihub_api && make lint)
	@(cd aihub_bot && make lint)
	@(cd aihub_iac && make lint)

# Format code with Black
format:
	@echo "Formatting code for pipelines..."
	@(cd aihub_pipeline && make format)
	@(cd aihub_lib && make format)
	@(cd aihub_agent && make format)
	@(cd aihub_process && make format)
	@(cd aihub_api && make format)
	@(cd aihub_bot && make format)
	@(cd aihub_iac && make format)

# Type-check with MyPy
typecheck:
	@echo "Running type checks for pipelines..."
	@(cd aihub_pipeline && make typecheck)
	@(cd aihub_lib && make typecheck)
	@(cd aihub_agent && make typecheck)
	@(cd aihub_process && make typecheck)
	@(cd aihub_api && make typecheck)
	@(cd aihub_bot && make typecheck)
	@(cd aihub_iac && make typecheck)

# Run format, type-check, and test in sequence
pr-ready:
	@echo "Running full check (format, lint)..."
	@(cd aihub_pipeline &&  make pr-ready)
	@(cd aihub_lib &&  make pr-ready)
	@(cd aihub_agent &&  make pr-ready)
	@(cd aihub_process &&  make pr-ready)
	@(cd aihub_api &&  make pr-ready)
	@(cd aihub_bot &&  make pr-ready)
	@(cd aihub_iac &&  make pr-ready)
	@(cd aihub_web && make pr-ready)
	@echo "Checking licenses..."
	@/bin/bash ./license-check.sh

# Use local cores for development
use-local-core:
	@echo "Switching to local cores..."
	poetry run python switch_dependencies.py local

TAG ?= v0.234.0

use-remote-core:
	@echo "Switching all microservices to remote with tag: $(TAG)"
	poetry run python switch_dependencies.py remote --tag "$(TAG)"

changelog:
	@echo "Generating changelog"
	/bin/bash ./generate-changelog.sh

# Check licenses across all dependencies
license-check:
	@echo "Checking licenses..."
	/bin/bash ./license-check.sh