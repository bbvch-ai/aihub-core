lint:
	@echo "Running linter..."
	@(cd aihub_pipeline && make lint)
	@(cd aihub_lib && make lint)
	@(cd aihub_agent && make lint)
	@(cd aihub_api && make lint)
	@(cd aihub_bot && make lint)

# Format code with Black
format:
	@echo "Formatting code for pipelines..."
	@(cd aihub_pipeline && make format)
	@(cd aihub_lib && make format)
	@(cd aihub_agent && make format)
	@(cd aihub_api && make format)
	@(cd aihub_bot && make format)

# Type-check with MyPy
typecheck:
	@echo "Running type checks for pipelines..."
	@(cd aihub_pipeline && make typecheck)
	@(cd aihub_lib && make typecheck)
	@(cd aihub_agent && make typecheck)
	@(cd aihub_api && make typecheck)
	@(cd aihub_bot && make typecheck)

# Sort imports with isort
sort-imports:
	@echo "Sorting imports for pipelines..."
	@(cd aihub_pipeline &&  make sort-imports)
	@(cd aihub_lib &&  make sort-imports)
	@(cd aihub_agent &&  make sort-imports)
	@(cd aihub_api &&  make sort-imports)
	@(cd aihub_bot &&  make sort-imports)

# Run format, sort-imports, type-check, and test in sequence
pr-ready:
	@echo "Running full check (format-pipelines, sort-imports)..."
	@(cd aihub_pipeline &&  make pr-ready)
	@(cd aihub_lib &&  make pr-ready)
	@(cd aihub_agent &&  make pr-ready)
	@(cd aihub_api &&  make pr-ready)
	@(cd aihub_bot &&  make pr-ready)

# Use local cores for development
use-local-core:
	@echo "Switching to local cores..."
	poetry run python switch_dependencies.py local

TAG ?= v0.107.0

use-remote-core:
	@echo "Switching all microservices to remote with tag: $(TAG)"
	poetry run python switch_dependencies.py remote --tag "$(TAG)"

