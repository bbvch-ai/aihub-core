"""Memory ids appear in thread event logs, so updating or deleting by id must check the id's owner and kind."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from swiss_ai_hub.core.infrastructure.mem0.mem0_service import Mem0Service
from swiss_ai_hub.core.infrastructure.mem0.memory_not_found_error import MemoryNotFoundError
from swiss_ai_hub.core.infrastructure.mem0.types.memory_type import MemoryType


def _stored(owner_id: str, memory_type: MemoryType) -> dict:
    return {"id": "m1", "user_id": owner_id, "metadata": {"_type": memory_type.value}}


@pytest.fixture
def mem0_service() -> Mem0Service:
    with (
        patch("swiss_ai_hub.core.infrastructure.mem0.mem0_service.PatchedAsyncMemory") as mock_memory_cls,
        patch("swiss_ai_hub.core.infrastructure.mem0.mem0_service.PatchedOpenAILLM"),
        patch("swiss_ai_hub.core.infrastructure.mem0.mem0_service.PatchedOpenAIEmbedding"),
        patch("swiss_ai_hub.core.infrastructure.mem0.mem0_service.PatchedMemoryGraph"),
    ):
        mock_memory = MagicMock()
        mock_memory.get = AsyncMock()
        mock_memory.delete = AsyncMock()
        mock_memory.update = AsyncMock()
        mock_memory_cls.return_value = mock_memory
        service = Mem0Service(config=MagicMock(), t=MagicMock())
    return service


@pytest.mark.asyncio
async def test_owner_can_delete_own_memory(mem0_service):
    mem0_service._memory.get.return_value = _stored("u1", MemoryType.USER_MEMORY)

    await mem0_service.delete_memory(memory_id="m1", owner_id="u1", memory_type=MemoryType.USER_MEMORY)

    mem0_service._memory.delete.assert_awaited_once_with("m1")


@pytest.mark.asyncio
async def test_owner_can_update_own_memory(mem0_service):
    mem0_service._memory.get.return_value = _stored("acme", MemoryType.ORGANIZATION_MEMORY)

    await mem0_service.update_memory(
        memory_id="m1", owner_id="acme", memory_type=MemoryType.ORGANIZATION_MEMORY, data="new"
    )

    mem0_service._memory.update.assert_awaited_once_with(memory_id="m1", data="new")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "stored",
    [
        None,
        _stored("someone-else", MemoryType.USER_MEMORY),
        _stored("u1", MemoryType.ORGANIZATION_MEMORY),
    ],
    ids=["unknown-id", "other-owner", "other-kind"],
)
async def test_delete_outside_scope_is_not_found(mem0_service, stored):
    mem0_service._memory.get.return_value = stored

    with pytest.raises(MemoryNotFoundError):
        await mem0_service.delete_memory(memory_id="m1", owner_id="u1", memory_type=MemoryType.USER_MEMORY)

    mem0_service._memory.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_of_another_tenants_memory_is_not_found(mem0_service):
    mem0_service._memory.get.return_value = _stored("tenant-b", MemoryType.ORGANIZATION_MEMORY)

    with pytest.raises(MemoryNotFoundError):
        await mem0_service.update_memory(
            memory_id="m1", owner_id="tenant-a", memory_type=MemoryType.ORGANIZATION_MEMORY, data="x"
        )

    mem0_service._memory.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_reassign_moves_owner_and_tenant_and_keeps_the_rest(mem0_service):
    vector_store = mem0_service._memory.vector_store = MagicMock()
    vector_store.list.return_value = [
        [SimpleNamespace(id="m1", payload={"user_id": "AIHub", "_tenant_id": "AIHub", "data": "fact"})]
    ]

    moved = await mem0_service.reassign_organization_memories(from_tenant_id="AIHub", to_tenant_id="default")

    assert moved == 1
    assert vector_store.list.call_args.kwargs["filters"] == {"user_id": "AIHub", "_type": "organization_memory"}
    vector_store.update.assert_called_once_with(
        vector_id="m1", payload={"user_id": "default", "_tenant_id": "default", "data": "fact"}
    )


def _legacy(memory_id: str) -> SimpleNamespace:
    return SimpleNamespace(id=memory_id, payload={"user_id": "AIHub", "_tenant_id": "AIHub"})


@pytest.mark.asyncio
async def test_reassign_continues_past_a_full_batch(mem0_service):
    vector_store = mem0_service._memory.vector_store = MagicMock()
    vector_store.list.side_effect = [[[_legacy("m1"), _legacy("m2")]], [[_legacy("m3")]]]

    with patch("swiss_ai_hub.core.infrastructure.mem0.mem0_service.REASSIGN_BATCH_SIZE", 2):
        moved = await mem0_service.reassign_organization_memories(from_tenant_id="AIHub", to_tenant_id="default")

    assert moved == 3
    assert vector_store.update.call_count == 3


@pytest.mark.asyncio
async def test_reassign_stops_when_a_full_batch_holds_only_moved_memories(mem0_service):
    vector_store = mem0_service._memory.vector_store = MagicMock()
    vector_store.list.side_effect = [[[_legacy("m1"), _legacy("m2")]], [[_legacy("m1"), _legacy("m2")]]]

    with patch("swiss_ai_hub.core.infrastructure.mem0.mem0_service.REASSIGN_BATCH_SIZE", 2):
        moved = await mem0_service.reassign_organization_memories(from_tenant_id="AIHub", to_tenant_id="default")

    assert moved == 2
    assert vector_store.list.call_count == 2


@pytest.mark.asyncio
async def test_reassign_to_the_same_tenant_does_nothing(mem0_service):
    vector_store = mem0_service._memory.vector_store = MagicMock()

    assert await mem0_service.reassign_organization_memories(from_tenant_id="AIHub", to_tenant_id="AIHub") == 0
    vector_store.list.assert_not_called()
