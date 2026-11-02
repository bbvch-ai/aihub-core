"""Unit tests for the search-query clamp (issue #1752).

An oversized query used to reach mem0's embedder verbatim and raise `ContextWindowExceededError`. The RAG
path caught it and silently answered without memory (issue #1713); the memory REST path had no such catch
and returned a 500. `Mem0Service.search` now truncates the query to the embedding budget (keeping the tail,
where the user's question lives) and logs a warning; queries within the budget pass through unchanged.
"""

import logging
from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.utils import get_tokenizer

from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_query_clamp import (
    MINIMUM_EMBEDDING_MAX_INPUT_TOKENS,
    QUERY_BUDGET_SAFETY_FACTOR,
)
from swiss_ai_hub.core.generative_ai.resources.models.llm.reranking_model_config import RerankingModelConfig
from swiss_ai_hub.core.generative_ai.resources.tokenizers.model_tokenizer import ModelTokenizer
from swiss_ai_hub.core.infrastructure.mem0.mem0_service import Mem0Service
from swiss_ai_hub.core.infrastructure.mem0.mem0_settings import Mem0Settings
from swiss_ai_hub.core.infrastructure.mem0.types.memory_search_result import MemorySearchResult
from swiss_ai_hub.core.infrastructure.mem0.types.memory_type import MemoryType

CLAMP_MODULE = "swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_query_clamp"
LIMIT = 64
EFFECTIVE_LIMIT = int(LIMIT * QUERY_BUDGET_SAFETY_FACTOR)


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
        config = MagicMock()
        config.embedder.config = {"model": "embedding/bge-m3"}
        config.reranker.config = {"model": "reranker/bge"}
        return Mem0Service(config=config, t=MagicMock(), max_search_query_tokens=max_search_query_tokens)


@pytest.fixture
def mem0_service() -> Iterator[Mem0Service]:
    """An embedder without a declared tokenizer, the case these tests pin: counted in tiktoken at half the window."""
    with _resolving_model_info({"mode": "embedding", "max_input_tokens": 8192}):
        yield _build_service(max_search_query_tokens=LIMIT)


def _resolving_model_info(model_info: dict):
    return patch.object(EmbeddingModelConfig, "get_model_info", return_value={"model_info": model_info})


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


@pytest.mark.parametrize("whitespace", [" \n\t", " ", "　"])
@pytest.mark.asyncio
async def test_oversized_whitespace_only_query_does_not_crash(mem0_service, whitespace):
    """Exotic whitespace does not compress under tiktoken (an Ogham space mark costs 3 tokens), so it
    clears the budget check. A sentence splitter dropped whitespace-only chunks and returned none, which
    raised IndexError on the tail lookup; the tail search always yields a non-empty, in-budget suffix."""
    query = whitespace * 4000

    await mem0_service.search(query=query, owner_id="owner", memory_type=MemoryType.USER_MEMORY)

    forwarded = _forwarded_query(mem0_service)
    assert forwarded
    assert len(get_tokenizer()(forwarded)) <= EFFECTIVE_LIMIT


@pytest.mark.asyncio
async def test_truncation_logs_warning_with_original_and_effective_lengths(mem0_service, caplog):
    query = "Document content sentence. " * 200

    with caplog.at_level(logging.WARNING, logger=CLAMP_MODULE):
        await mem0_service.search(query=query, owner_id="owner", memory_type=MemoryType.USER_MEMORY)

    record = next(r for r in caplog.records if "truncating" in r.message)
    original_tokens, effective_tokens = record.args[0], record.args[1]
    assert original_tokens == len(get_tokenizer()(query))
    assert effective_tokens <= EFFECTIVE_LIMIT
    assert record.args[4] == EFFECTIVE_LIMIT


@pytest.mark.asyncio
async def test_normal_query_passes_through_identical(mem0_service, caplog):
    query = "What is the retention period?"

    with caplog.at_level(logging.WARNING, logger=CLAMP_MODULE):
        await mem0_service.search(query=query, owner_id="owner", memory_type=MemoryType.USER_MEMORY)

    assert _forwarded_query(mem0_service) is query
    assert not caplog.records


@pytest.mark.asyncio
async def test_query_at_the_token_budget_passes_through_identical(mem0_service):
    query = "word " * EFFECTIVE_LIMIT
    while len(get_tokenizer()(query)) > EFFECTIVE_LIMIT:
        query = query[:-5]

    await mem0_service.search(query=query, owner_id="owner", memory_type=MemoryType.USER_MEMORY)

    assert len(get_tokenizer()(query)) == EFFECTIVE_LIMIT
    assert _forwarded_query(mem0_service) is query


@pytest.mark.asyncio
async def test_query_short_in_characters_but_over_budget_in_tokens_is_clamped(mem0_service):
    """A character is not an upper bound on tokens: a ZWJ emoji sequence costs 7. A character-based
    short-circuit let such a query reach the embedder at twice its budget."""
    query = "\U0001f600" * (EFFECTIVE_LIMIT - 1)

    await mem0_service.search(query=query, owner_id="owner", memory_type=MemoryType.USER_MEMORY)

    forwarded = _forwarded_query(mem0_service)
    assert len(query) < EFFECTIVE_LIMIT
    assert len(get_tokenizer()(query)) > EFFECTIVE_LIMIT
    assert len(get_tokenizer()(forwarded)) <= EFFECTIVE_LIMIT


@pytest.mark.asyncio
async def test_query_under_the_default_window_is_clamped_to_a_smaller_resolved_window():
    """A resolution-free floor derived from the 8192 default would let a query that is short in characters
    but long for a small embedding model reach the embedder un-clamped — the exact crash this guards."""
    service = _build_service(max_search_query_tokens=None)
    small_window = 512
    query = "Document content sentence. " * 200

    with _resolving_model_info({"mode": "embedding", "max_input_tokens": small_window}):
        await service.search(query=query, owner_id="owner", memory_type=MemoryType.USER_MEMORY)

    forwarded = _forwarded_query(service)
    assert len(get_tokenizer()(query)) < int(8192 * QUERY_BUDGET_SAFETY_FACTOR)
    assert forwarded is not query
    assert len(get_tokenizer()(forwarded)) <= int(small_window * QUERY_BUDGET_SAFETY_FACTOR)


@pytest.mark.asyncio
async def test_query_within_the_minimum_window_budget_skips_resolution():
    service = _build_service(max_search_query_tokens=None)
    budget = int(MINIMUM_EMBEDDING_MAX_INPUT_TOKENS * QUERY_BUDGET_SAFETY_FACTOR)
    query = "word " * budget
    while len(get_tokenizer()(query)) > budget:
        query = query[:-5]

    with patch.object(EmbeddingModelConfig, "get_model_info", side_effect=AssertionError("resolved")):
        await service.search(query=query, owner_id="owner", memory_type=MemoryType.USER_MEMORY)

    assert _forwarded_query(service) is query


def test_settings_field_defaults_to_none():
    settings = Mem0Settings(LLM_NAME="llm", EMBEDDING_MODEL_NAME="embed", RERANKING_MODEL_NAME="rerank")
    assert settings.SEARCH_QUERY_EMBEDDING_WINDOW is None


def test_settings_field_parses_from_env(monkeypatch):
    monkeypatch.setenv("MEM0_SEARCH_QUERY_EMBEDDING_WINDOW", "4096")
    settings = Mem0Settings(LLM_NAME="llm", EMBEDDING_MODEL_NAME="embed", RERANKING_MODEL_NAME="rerank")
    assert settings.SEARCH_QUERY_EMBEDDING_WINDOW == 4096


@pytest.mark.asyncio
async def test_declared_embedder_counts_the_query_in_its_own_tokens():
    service = _build_service(max_search_query_tokens=LIMIT)
    query = "Document content sentence. " * 200
    declared = {"mode": "embedding", "aihub_tokenizer": "bge-m3", "aihub_input_overhead_tokens": 2}

    with _resolving_model_info(declared):
        await service.search(query=query, owner_id="owner", memory_type=MemoryType.USER_MEMORY)

    assert ModelTokenizer.shared("bge-m3").count(_forwarded_query(service)) <= LIMIT - 2


DECLARED_EMBEDDER = {
    "mode": "embedding",
    "max_input_tokens": 8192,
    "aihub_tokenizer": "bge-m3",
    "aihub_input_overhead_tokens": 2,
}
DECLARED_RERANKER = {
    "mode": "rerank",
    "max_input_tokens": 8192,
    "aihub_tokenizer": "bge-m3",
    "aihub_input_overhead_tokens": 4,
}
MEMORY = "The user prefers concise answers in German."
QUESTION = "What did I say about the notice period?"


def _declared_embedder_and_reranker():
    return (
        patch.object(EmbeddingModelConfig, "get_model_info", return_value={"model_info": DECLARED_EMBEDDER}),
        patch.object(RerankingModelConfig, "get_model_info", return_value={"model_info": DECLARED_RERANKER}),
    )


@pytest.mark.asyncio
async def test_a_reranked_search_leaves_the_reranker_room_for_the_memory():
    """mem0 reranks each memory with the query in one window, through its own reranker rather than rerank_nodes; a
    query filling the embedder's window left no room for the memory, and every long search lost its reranking."""
    service = _build_service(max_search_query_tokens=None)
    query = ("Clause text from the attached contract. " * 2600) + QUESTION
    embedder, reranker = _declared_embedder_and_reranker()

    with embedder, reranker:
        await service.search(query=query, owner_id="owner", memory_type=MemoryType.USER_MEMORY)

    count = ModelTokenizer.shared("bge-m3").count
    forwarded = _forwarded_query(service)
    assert count(forwarded) + DECLARED_RERANKER["aihub_input_overhead_tokens"] + count(MEMORY) <= 8192
    assert forwarded.endswith(QUESTION)


@pytest.mark.asyncio
async def test_a_search_without_reranking_keeps_the_embedders_whole_window():
    service = _build_service(max_search_query_tokens=None)
    query = "Clause text from the attached contract. " * 2600
    embedder, reranker = _declared_embedder_and_reranker()

    with embedder, reranker:
        await service.search(query=query, owner_id="owner", memory_type=MemoryType.USER_MEMORY, rerank=False)

    assert ModelTokenizer.shared("bge-m3").count(_forwarded_query(service)) > 8192 - 100
