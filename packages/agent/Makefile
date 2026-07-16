-include ../../.env
export

lint:
	@echo "Running linter..."
	uv run ruff check --fix

# Format code with Black
format:
	@echo "Formatting code..."
	uv run ruff format

# Type-check with ty
typecheck:
	@echo "Running type checks..."
	uv run ty check

test-cov:
	@echo "Running tests in swiss_ai_hub.agent with coverage..."
	uv run pytest --cov=. \
	                  --cov-report=xml:coverage.xml \
	                  --cov-report=term-missing \
	                  --junitxml=pytest.xml

test:
	@echo "Running tests in swiss_ai_hub.agent..."
	uv run pytest

pr-ready: format lint
	@echo "Running full check (format, sort)..."

run-rag-agent:
	uv run python app/rag_agent/main.py

run-expert-asking-agent:
	uv run python app/expert_asking_agent/main.py

run-expert-rag-agent:
	uv run python app/expert_rag_agent/main.py

run-few-shot-agent:
	uv run python app/few_shot_agent/main.py

run-llm-wrapping-agent:
	uv run python app/llm_wrapping_agent/main.py

run-namespace-selection-agent:
	uv run python app/namespace_selection_agent/main.py

run-retrieval-agent:
	uv run python app/retrieval_agent/main.py

run-memory-writer-agent:
	uv run python app/memory_writer_agent/main.py

run-imap-agent:
	uv run python app/imap_agent/main.py