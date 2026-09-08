"""Unit tests for the search-query clamp (issue #1752).

An oversized query used to reach mem0's embedder verbatim and raise `ContextWindowExceededError`, aborting
the whole agent run. `Mem0Service.search` now truncates the query to the embedding budget (keeping the tail,
where the user's question lives) and logs a warning; queries within the budget must pass through as the
identical object.
"""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.utils import get_tokenizer

from swiss_ai_hub.core.infrastructure.mem0.mem0_service import (
    EMBEDDING_BUDGET_SAFETY_FACTOR,
    Mem0Service,
)
from swiss_ai_hub.core.infrastructure.mem0.mem0_settings import Mem0Settings
from swiss_ai_hub.core.infrastructure.mem0.types.memory_search_result import MemorySearchResult
from swiss_ai_hub.core.infrastructure.mem0.types.memory_type import MemoryType

LIMIT = 64
EFFECTIVE_LIMIT = int(LIMIT * EMBEDDING_BUDGET_SAFETY_FACTOR)


def _build_service(max_search_query_tokens: int | None) -> Mem0Service:
    """Build a Mem0Service with all heavy collaborators mocked out."""
    with (
        patch("swiss_ai_hub.core.infrastructure.mem0.mem0_service.PatchedAsyncMemory") as mock_memory_cls,
        patch("swiss_ai_hub.core.infrastructure.mem0.mem0_service.PatchedOpenAILLM"),
        patch("swiss_ai_hub.core.infrastructure.mem0.mem0_service.PatchedOpenAIEmbedding"),
        patch("swiss_ai_hub.core.infrastructure.mem0.mem0_service.PatchedMemoryGraph"),
    ):
        mock_memory = MagicMock()
        mock_memory.search = AsyncMock(return_value={"results": [], "relations": []})
        mock_memory_cls.return_value = mock_memory
        return Mem0Service(config=MagicMock(), t=MagicMock(), max_search_query_tokens=max_search_query_tokens)


@pytest.fixture
def mem0_service() -> Mem0Service:
    return _build_service(max_search_query_tokens=LIMIT)


def _forwarded_query(service: Mem0Service) -> str:
    return service._memory.search.await_args.kwargs["query"]


@pytest.mark.asyncio
async def test_oversized_query_is_truncated_and_search_succeeds(mem0_service):
    question = "What is the retention period?"
    query = ("Document content sentence. " * 200) + question

    result = await mem0_service.search(query=query, owner_id="owner", memory_type=MemoryType.USER_MEMORY)

    forwarded = _forwarded_query(mem0_service)
    assert isinstance(result, MemorySearchResult)
    assert forwarded != query
    assert len(get_tokenizer()(forwarded)) <= EFFECTIVE_LIMIT
    assert forwarded.endswith(question)


@pytest.mark.asyncio
async def test_oversized_query_without_whitespace_is_still_truncated(mem0_service):
    query = "".join(f"word{i}" for i in range(500))

    await mem0_service.search(query=query, owner_id="owner", memory_type=MemoryType.USER_MEMORY)

    forwarded = _forwarded_query(mem0_service)
    assert forwarded
    assert len(get_tokenizer()(forwarded)) <= EFFECTIVE_LIMIT


@pytest.mark.asyncio
async def test_truncation_logs_warning_with_original_and_effective_lengths(mem0_service, caplog):
    query = "Document content sentence. " * 200

    with caplog.at_level(logging.WARNING, logger="swiss_ai_hub.core.infrastructure.mem0.mem0_service"):
        await mem0_service.search(query=query, owner_id="owner", memory_type=MemoryType.USER_MEMORY)

    record = next(r for r in caplog.records if "truncating" in r.message)
    original_tokens, effective_tokens = record.args[0], record.args[1]
    assert original_tokens == len(get_tokenizer()(query))
    assert effective_tokens <= EFFECTIVE_LIMIT
    assert record.args[4] == EFFECTIVE_LIMIT


@pytest.mark.asyncio
async def test_normal_query_passes_through_identical(mem0_service, caplog):
    query = "What is the retention period?"

    with caplog.at_level(logging.WARNING, logger="swiss_ai_hub.core.infrastructure.mem0.mem0_service"):
        await mem0_service.search(query=query, owner_id="owner", memory_type=MemoryType.USER_MEMORY)

    assert _forwarded_query(mem0_service) is query
    assert not caplog.records


@pytest.mark.asyncio
async def test_query_at_the_character_floor_passes_through_identical(mem0_service):
    query = "a" * EFFECTIVE_LIMIT

    await mem0_service.search(query=query, owner_id="owner", memory_type=MemoryType.USER_MEMORY)

    assert _forwarded_query(mem0_service) is query


def test_lazy_default_resolves_the_model_window():
    service = _build_service(max_search_query_tokens=None)
    with patch("swiss_ai_hub.core.infrastructure.mem0.mem0_service.EmbeddingModelConfig") as config_cls:
        config_cls.return_value.get_model_info.return_value = {"model_info": {"max_input_tokens": 100}}
        assert service._effective_query_token_limit == int(100 * EMBEDDING_BUDGET_SAFETY_FACTOR)


def test_null_model_window_falls_back_to_default():
    service = _build_service(max_search_query_tokens=None)
    with patch("swiss_ai_hub.core.infrastructure.mem0.mem0_service.EmbeddingModelConfig") as config_cls:
        config_cls.return_value.get_model_info.return_value = {"model_info": {"max_input_tokens": None}}
        assert service._effective_query_token_limit == int(8192 * EMBEDDING_BUDGET_SAFETY_FACTOR)


def test_explicit_limit_never_resolves_model_info():
    service = _build_service(max_search_query_tokens=LIMIT)
    with patch("swiss_ai_hub.core.infrastructure.mem0.mem0_service.EmbeddingModelConfig") as config_cls:
        assert service._effective_query_token_limit == EFFECTIVE_LIMIT
        config_cls.assert_not_called()


def test_settings_field_defaults_to_none():
    settings = Mem0Settings(LLM_NAME="llm", EMBEDDING_MODEL_NAME="embed", RERANKING_MODEL_NAME="rerank")
    assert settings.SEARCH_QUERY_MAX_TOKENS is None


def test_settings_field_parses_from_env(monkeypatch):
    monkeypatch.setenv("MEM0_SEARCH_QUERY_MAX_TOKENS", "4096")
    settings = Mem0Settings(LLM_NAME="llm", EMBEDDING_MODEL_NAME="embed", RERANKING_MODEL_NAME="rerank")
    assert settings.SEARCH_QUERY_MAX_TOKENS == 4096
