"""Unit tests for Mem0Service.search filter-dict construction.

Verifies the namespace allow-list translates into the correct mem0 filter
shape: empty/None → no `_tenant_namespace` filter; single → bare string
equality; multiple → `{"in": [...]}` advanced operator.
"""

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
