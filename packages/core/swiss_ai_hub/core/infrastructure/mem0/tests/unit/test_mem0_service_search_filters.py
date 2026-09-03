"""Unit tests for Mem0Service.search filter-dict construction.

Verifies the namespace allow-list translates into the correct mem0 filter
shape: empty/None → no `_tenant_namespace` filter; single → bare string
equality; multiple → `{"in": [...]}` advanced operator.
"""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from swiss_ai_hub.core.infrastructure.mem0.mem0_service import Mem0Service
from swiss_ai_hub.core.infrastructure.mem0.types.memory_type import MemoryType


@pytest.fixture
def mem0_service() -> Mem0Service:
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
        service = Mem0Service(config=MagicMock(), t=MagicMock())
        service._memory.embedding_model._tokenizer = MagicMock()
        service._memory.embedding_model._tokenizer.encode.side_effect = lambda value: list(value)
        service._memory.embedding_model._tokenizer.decode.side_effect = lambda value: "".join(value)
    return service


def _captured_filters(service: Mem0Service) -> dict:
    """Return the `filters` kwarg from the most recent _memory.search call."""
    call = service._memory.search.await_args
    return call.kwargs["filters"]


@pytest.mark.asyncio
async def test_no_namespaces_omits_tenant_namespace_filter(mem0_service):
    await mem0_service.search(
        query="q",
        owner_id="owner",
        memory_type=MemoryType.ORGANIZATION_MEMORY,
        tenant_id="ACME",
        tenant_namespaces=None,
    )
    filters = _captured_filters(mem0_service)
    assert "_tenant_namespace" not in filters
    assert filters["_tenant_id"] == "ACME"
    assert mem0_service._memory.search.await_args.kwargs["query"] == "q"


@pytest.mark.asyncio
async def test_oversized_query_is_truncated_and_logged(mem0_service, caplog):
    mem0_service._embedding_max_input_tokens = 3
    mem0_service._memory.embedding_model._tokenizer.encode.side_effect = lambda value: list(value)
    mem0_service._memory.embedding_model._tokenizer.decode.side_effect = lambda value: "".join(value)

    with caplog.at_level(logging.WARNING):
        await mem0_service.search(
            query="abcdef",
            owner_id="owner",
            memory_type=MemoryType.ORGANIZATION_MEMORY,
        )

    assert mem0_service._memory.search.await_args.kwargs["query"] == "abc"
    assert "from 6 to 3 tokens" in caplog.text


@pytest.mark.asyncio
async def test_empty_namespaces_omits_tenant_namespace_filter(mem0_service):
    await mem0_service.search(
        query="q",
        owner_id="owner",
        memory_type=MemoryType.ORGANIZATION_MEMORY,
        tenant_id="ACME",
        tenant_namespaces=[],
    )
    filters = _captured_filters(mem0_service)
    assert "_tenant_namespace" not in filters


@pytest.mark.asyncio
async def test_single_namespace_uses_bare_equality(mem0_service):
    await mem0_service.search(
        query="q",
        owner_id="owner",
        memory_type=MemoryType.ORGANIZATION_MEMORY,
        tenant_id="ACME",
        tenant_namespaces=["dept-x"],
    )
    filters = _captured_filters(mem0_service)
    assert filters["_tenant_namespace"] == "dept-x"


@pytest.mark.asyncio
async def test_multiple_namespaces_uses_in_operator(mem0_service):
    await mem0_service.search(
        query="q",
        owner_id="owner",
        memory_type=MemoryType.ORGANIZATION_MEMORY,
        tenant_id="ACME",
        tenant_namespaces=["dept-x", "dept-y", "dept-z"],
    )
    filters = _captured_filters(mem0_service)
    assert filters["_tenant_namespace"] == {"in": ["dept-x", "dept-y", "dept-z"]}
