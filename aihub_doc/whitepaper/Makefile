# Whitepaper Generation Makefile
#
# Usage:
#   make pdf          - Generate whitepaper.pdf from output/*.md
#   make clean        - Remove generated files
#   make sources      - Run LLM source discovery
#   make chapters     - Generate all chapters
#   make all          - Full pipeline: sources -> chapters -> pdf

SHELL := /bin/bash

# Output files
PDF := whitepaper.pdf

# Source files
TEMPLATE := whitepaper.tex
METADATA := metadata.yaml

.PHONY: all pdf clean sources chapters help

# Default target
all: sources chapters pdf

# Generate PDF from markdown chapters (wildcard auto-includes new chapters)
pdf:
	@echo "📕 Generating PDF with pandoc..."
	pandoc output/*_output.md \
		--metadata-file=$(METADATA) \
		--template=$(TEMPLATE) \
		--pdf-engine=xelatex \
		-o $(PDF)
	@echo "✅ Generated $(PDF)"

# Run LLM source discovery
sources:
	@echo "🔍 Running source discovery..."
	$(PYTHON) generate-sources.py

# Generate all chapters
chapters:
	@echo "📝 Generating chapters..."
	$(PYTHON) generate-whitepaper.py

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
	@echo "Prerequisites:"
	@echo "  - pandoc with xelatex"
	@echo "  - Python 3 with jinja2"
	@echo "  - llm CLI tool configured"
