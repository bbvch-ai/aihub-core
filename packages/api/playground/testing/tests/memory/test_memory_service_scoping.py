"""The memory services confine every call to the caller: organization memory to the acting tenant, user memory to
the user, and a memory id outside that scope answers 404 rather than revealing that it exists."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from swiss_ai_hub.core.infrastructure import MemoryNotFoundError
from swiss_ai_hub.core.testing.auth_utils import fake_user

from swiss_ai_hub.api.routes.memory.organization_memory_service import OrganizationMemoryService
from swiss_ai_hub.api.routes.memory.user_memory_service import UserMemoryService

ORG_MEMORY = "swiss_ai_hub.api.routes.memory.organization_memory_service.OrganizationMemory"
USER_MEMORY = "swiss_ai_hub.api.routes.memory.user_memory_service.UserMemory"


def _memory_raising_not_found() -> MagicMock:
    memory = MagicMock()
    memory.delete_memory = AsyncMock(side_effect=MemoryNotFoundError("m1"))
    memory.update_memory = AsyncMock(side_effect=MemoryNotFoundError("m1"))
    return memory


@pytest.mark.asyncio
async def test_organization_memory_is_opened_for_the_callers_tenant():
    memory = MagicMock()
    memory.delete_all = AsyncMock()
    with patch(ORG_MEMORY, return_value=memory) as organization_memory_class:
        await OrganizationMemoryService.delete_all_memories(tenant_id="tenant-a", t=MagicMock())

    assert organization_memory_class.call_args.kwargs["tenant_id"] == "tenant-a"
    memory.delete_all.assert_awaited_once()


@pytest.mark.asyncio
async def test_deleting_an_organization_memory_outside_the_tenant_is_404():
    with patch(ORG_MEMORY, return_value=_memory_raising_not_found()), pytest.raises(HTTPException) as exc_info:
        await OrganizationMemoryService.delete_memory(tenant_id="tenant-a", memory_id="m1", t=MagicMock())

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_updating_an_organization_memory_outside_the_tenant_is_404():
    with patch(ORG_MEMORY, return_value=_memory_raising_not_found()), pytest.raises(HTTPException) as exc_info:
        await OrganizationMemoryService.update_memory(tenant_id="tenant-a", memory_id="m1", data="x", t=MagicMock())

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_deleting_another_users_memory_is_404():
    with patch(USER_MEMORY, return_value=_memory_raising_not_found()), pytest.raises(HTTPException) as exc_info:
        await UserMemoryService.delete_memory(user=fake_user(), memory_id="m1", t=MagicMock())

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_updating_another_users_memory_is_404():
    with patch(USER_MEMORY, return_value=_memory_raising_not_found()), pytest.raises(HTTPException) as exc_info:
        await UserMemoryService.update_memory(user=fake_user(), memory_id="m1", data="x", t=MagicMock())

    assert exc_info.value.status_code == 404
