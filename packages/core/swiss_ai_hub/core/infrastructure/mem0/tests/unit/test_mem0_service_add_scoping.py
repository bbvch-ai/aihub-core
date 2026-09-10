"""Unit tests for Mem0Service.add_memory native-agent_id scoping.

User memory must pass mem0's native `agent_id` so infer-time reconciliation
(ADD/UPDATE/DELETE over existing memories) is scoped to the writing agent — one
agent can no longer rewrite or delete another agent's user memories. Organization
memory stays unscoped (native `agent_id` omitted), matching its intentionally
tenant-shared behavior.
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
        mock_memory.add = AsyncMock(return_value={"results": []})
        mock_memory_cls.return_value = mock_memory
        service = Mem0Service(config=MagicMock(), t=MagicMock())
    return service


def _captured_native_agent_id(service: Mem0Service):
    """Return the native `agent_id` kwarg from the most recent _memory.add call."""
    return service._memory.add.await_args.kwargs["agent_id"]


@pytest.mark.asyncio
async def test_user_memory_add_passes_native_agent_id(mem0_service):
    await mem0_service.add_memory(
        messages=[{"role": "user", "content": "I prefer Python", "name": "u1"}],
        owner_id="u1",
        memory_type=MemoryType.USER_MEMORY,
        user_id="u1",
        agent_id="rag_agent/1",
        thread_id="t1",
        display_id="d1",
        run_id="r1",
    )
    assert _captured_native_agent_id(mem0_service) == "rag_agent/1"


@pytest.mark.asyncio
async def test_org_memory_add_omits_native_agent_id(mem0_service):
    await mem0_service.add_memory(
        messages=[{"role": "user", "content": "Company policy X", "name": "u1"}],
        owner_id="ACME",
        memory_type=MemoryType.ORGANIZATION_MEMORY,
        user_id="u1",
        agent_id="rag_agent/1",
        thread_id="t1",
        display_id="d1",
        run_id="r1",
        tenant_id="ACME",
        tenant_namespace="dept-x",
        infer=False,
    )
    assert _captured_native_agent_id(mem0_service) is None
