# Whitepaper Generation Makefile
#
# Usage:
#   make pdf          - Generate whitepaper.pdf from chapters/*/output.md
#   make clean        - Remove generated files
#   make sources      - Run LLM source discovery
#   make chapters     - Generate all chapters
#   make all          - Full pipeline: sources -> chapters -> pdf

SHELL := /bin/bash

# Directories
SCRIPTS_DIR := scripts
CONFIG_DIR := config
BUILD_DIR := build
CHAPTERS_DIR := chapters

# Output files
PDF := $(BUILD_DIR)/whitepaper.pdf

# Source files
TEMPLATE := $(BUILD_DIR)/whitepaper.tex
METADATA := $(CONFIG_DIR)/metadata.yaml

.PHONY: all pdf clean sources chapters help

# Default target
all: sources chapters pdf

# Current date (e.g., "03.02.2026")
DATE := $(shell date +"%d.%m.%Y")

# Generate PDF from markdown chapters (wildcard auto-includes new chapters)
pdf:
	@echo "📕 Generating PDF with pandoc..."
	@echo "   Date: $(DATE)"
	pandoc $(CHAPTERS_DIR)/*/output.md \
		--metadata-file=$(METADATA) \
		--metadata date="$(DATE)" \
		--template=$(TEMPLATE) \
		--pdf-engine=xelatex \
		-o $(PDF)
	@echo "✅ Generated $(PDF)"

# Run LLM source discovery
sources:
	@echo "🔍 Running source discovery..."
	$(PYTHON) $(SCRIPTS_DIR)/generate-sources.py

# Generate all chapters
chapters:
	@echo "📝 Generating chapters..."
	$(PYTHON) $(SCRIPTS_DIR)/generate-whitepaper.py

# Clean generated files
clean:
	@echo "🧹 Cleaning..."
	rm -f $(PDF)

# Help
help:
	@echo "Whitepaper Generation"
	@echo ""
	@echo "Targets:"
	@echo "  make pdf       - Generate PDF from existing chapters"
	@echo "  make sources   - Run LLM source discovery"
	@echo "  make chapters  - Generate all whitepaper chapters"
	@echo "  make all       - Full pipeline (sources -> chapters -> pdf)"
	@echo "  make clean     - Remove generated files"
	@echo ""
	@echo "Directory Structure:"
	@echo "  chapters/      - Chapter folders (prompt.md, sources.md, output.md)"
	@echo "  config/        - Configuration (glossary.md, general_prompt.md, metadata.yaml)"
	@echo "  scripts/       - Generation scripts"
	@echo "  build/         - Build output (whitepaper.pdf, whitepaper.tex)"
	@echo ""
	@echo "Prerequisites:"
	@echo "  - pandoc with xelatex"
	@echo "  - Python 3 with jinja2"
	@echo "  - llm CLI tool configured"
