lint:
	@echo "Running linter..."
	@(cd aihub_pipeline && make lint)
	@(cd aihub_lib && make lint)

# Format code with Black
format:
	@echo "Formatting code for pipelines..."
	@(cd aihub_pipeline && make format)
	@(cd aihub_lib && make format)

# Type-check with MyPy
typecheck:
	@echo "Running type checks for pipelines..."
	@(cd aihub_pipeline && make typecheck)
	@(cd aihub_lib && make typecheck)

# Sort imports with isort
sort-imports:
	@echo "Sorting imports for pipelines..."
	@(cd aihub_pipeline &&  make sort-imports)
	@(cd aihub_lib &&  make sort-imports)

# Run format, sort-imports, type-check, and test in sequence
pr-ready:
	@echo "Running full check (format-pipelines, sort-imports)..."
	@(cd aihub_pipeline &&  make pr-ready)
	@(cd aihub_lib &&  make pr-ready)