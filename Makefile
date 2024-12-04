lint:
	@echo "Running linter..."
	@(cd pipelines_core && make lint)

# Format code with Black
format:
	@echo "Formatting code for pipelines..."
	@(cd pipelines_core && make format)

# Type-check with MyPy
typecheck:
	@echo "Running type checks for pipelines..."
	@(cd pipelines_core && make typecheck)

# Sort imports with isort
sort-imports:
	@echo "Sorting imports for pipelines..."
	@(cd pipelines_core &&  make sort-imports)

# Run format, sort-imports, type-check, and test in sequence
pr-ready:
	@echo "Running full check (format-pipelines, sort-imports)..."
	@(cd pipelines_core &&  make pr-ready)