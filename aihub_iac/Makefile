lint:
	@echo "Running linter for pipelines..."
	poetry run ruff check --fix

format:
	@echo "Formatting code for pipelines..."
	poetry run ruff format

typecheck:
	@echo "Running type checks for pipelines..."
	poetry run mypy .

sort-imports:
	@echo "Sorting imports for pipelines..."
	poetry run isort .

pr-ready: sort-imports format lint
	@echo "Running full check (format, sort)..."

.PHONY: mirror help

# Mirror an image from source to target
# Usage: make mirror SOURCE=source/image:tag TARGET=target/image:tag
mirror-image:
	@if [ -z "$(SOURCE)" ] || [ -z "$(TARGET)" ]; then \
		echo "Error: SOURCE and TARGET parameters are required"; \
		echo "Usage: make mirror SOURCE=source/image:tag TARGET=target/image:tag"; \
		exit 1; \
	fi
	@echo "Mirroring $(SOURCE) to $(TARGET)..."
	@docker login ghcr.io
	@docker pull $(SOURCE)
	@docker tag $(SOURCE) $(TARGET)
	@docker push $(TARGET)
	@echo "Successfully mirrored $(SOURCE) to $(TARGET)"
