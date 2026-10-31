from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from swiss_ai_hub.api.routes.role.dto.create_role_request import CreateRoleRequest
from swiss_ai_hub.api.routes.role.dto.update_role_request import UpdateRoleRequest
from swiss_ai_hub.api.routes.role.role_service import RoleService

_ROLE_SERVICE = "swiss_ai_hub.api.routes.role.role_service"


class TestUpdateRolePersistsViaSave:
    """Regression: update_role must persist through the document (``save_changes()``), not a query update,
    otherwise the document event never fires and AccessChangeHook never re-syncs OpenWebUI access grants."""

    @pytest.mark.asyncio
    async def test_update_role_calls_save_not_modify(self):
        role = MagicMock()
        role.save_changes = AsyncMock()
        role.tenant_id = "tenant-1"

        with (
            patch(f"{_ROLE_SERVICE}.RoleEntity", new_callable=AsyncMock) as mock_entity,
            patch(f"{_ROLE_SERVICE}.RoleResponse"),
        ):
            mock_entity.get.return_value = role
            await RoleService.update_role(
                role_id="role-1",
                data=UpdateRoleRequest(access_rules=["aihub.user.model.text-generation.>"]),
                tenant_id="tenant-1",
            )

        role.save_changes.assert_awaited_once()
        role.modify.assert_not_called()
        assert role.access_rules == ["aihub.user.model.text-generation.>"]


class TestNormalizesModelAccessRulesOnWrite:
    """Model names carry version dots (``Kimi-K2.6``) that the checker collapses to ``_``; a rule
    written with the raw dot can never match, so the write path normalizes the model segment."""

    @pytest.mark.asyncio
    async def test_update_role_normalizes_dotted_model_name(self):
        role = MagicMock()
        role.save_changes = AsyncMock()
        role.tenant_id = "tenant-1"

        with (
            patch(f"{_ROLE_SERVICE}.RoleEntity", new_callable=AsyncMock) as mock_entity,
            patch(f"{_ROLE_SERVICE}.RoleResponse"),
        ):
            mock_entity.get.return_value = role
            await RoleService.update_role(
                role_id="role-1",
                data=UpdateRoleRequest(access_rules=["aihub.user.model.text-generation.Kimi-K2.6"]),
                tenant_id="tenant-1",
            )

        assert role.access_rules == ["aihub.user.model.text-generation.Kimi-K2_6"]

    @pytest.mark.asyncio
    async def test_create_role_normalizes_dotted_model_name(self):
        with (
            patch(f"{_ROLE_SERVICE}.RoleEntity", new_callable=AsyncMock) as mock_entity,
            patch(f"{_ROLE_SERVICE}.RoleResponse"),
        ):
            await RoleService.create_role(
                data=CreateRoleRequest(
                    name="R1",
                    description="d",
                    access_rules=["aihub.user.model.text-generation.Kimi-K2.6"],
                ),
                tenant_id="tenant-1",
            )

        passed_rules = mock_entity.create_tenant_role.call_args.kwargs["access_rules"]
        assert passed_rules == ["aihub.user.model.text-generation.Kimi-K2_6"]


class TestRejectsRoleRename:
    """Users are assigned roles by name, so renaming a role would leave every assignment pointing at a
    name that no longer exists."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("new_name", ["Demo Admin", None])
    async def test_update_role_rejects_changed_name(self, new_name: str | None):
        role = MagicMock()
        role.save_changes = AsyncMock()
        role.tenant_id = "tenant-1"
        role.name = "Admin"

        with (
            patch(f"{_ROLE_SERVICE}.RoleEntity", new_callable=AsyncMock) as mock_entity,
            patch(f"{_ROLE_SERVICE}.RoleResponse"),
            pytest.raises(HTTPException) as raised,
        ):
            mock_entity.get.return_value = role
            await RoleService.update_role(
                role_id="role-1",
                data=UpdateRoleRequest(name=new_name),
                tenant_id="tenant-1",
            )

        assert raised.value.status_code == 400
        role.save_changes.assert_not_awaited()
        assert role.name == "Admin"

    @pytest.mark.asyncio
    async def test_update_role_accepts_unchanged_name(self):
        role = MagicMock()
        role.save_changes = AsyncMock()
        role.tenant_id = "tenant-1"
        role.name = "Admin"

        with (
            patch(f"{_ROLE_SERVICE}.RoleEntity", new_callable=AsyncMock) as mock_entity,
            patch(f"{_ROLE_SERVICE}.RoleResponse"),
        ):
            mock_entity.get.return_value = role
            await RoleService.update_role(
                role_id="role-1",
                data=UpdateRoleRequest(name="Admin", description="new description"),
                tenant_id="tenant-1",
            )

        role.save_changes.assert_awaited_once()
        assert role.description == "new description"
