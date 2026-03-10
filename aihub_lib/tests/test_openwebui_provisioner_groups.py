"""Tests for OpenWebuiProvisioner — group sync logic."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner import (
    AIHUB_GROUP_PREFIX,
    OpenWebuiProvisioner,
)


@pytest.fixture
def mock_settings() -> MagicMock:
    settings = MagicMock()
    settings.BASE_URL = "http://open-webui:8080"
    settings.SECRET_KEY = MagicMock()
    settings.SECRET_KEY.get_secret_value.return_value = "sk-test"
    settings.SCIM_TOKEN = MagicMock()
    settings.SCIM_TOKEN.get_secret_value.return_value = "scim-test"
    return settings


@pytest.fixture
def provisioner(mock_settings: MagicMock) -> OpenWebuiProvisioner:
    return OpenWebuiProvisioner(settings=mock_settings)


def _ok_response(status_code: int = 200, json_data: dict | list | None = None) -> httpx.Response:
    return httpx.Response(
        status_code=status_code,
        json=json_data if json_data is not None else {},
        request=httpx.Request("GET", "http://test"),
    )


class TestBuildDesiredGroups:
    def test_build_desired_groups_single_tenant_single_role(self) -> None:
        tenants = [{"name": "TenantA"}]
        roles_by_tenant = {"TenantA": [{"name": "RoleA"}]}

        result = OpenWebuiProvisioner._build_desired_groups(tenants, roles_by_tenant)

        assert result == {f"{AIHUB_GROUP_PREFIX}TenantA:RoleA"}

    def test_build_desired_groups_cross_product(self) -> None:
        tenants = [{"name": "T1"}, {"name": "T2"}]
        roles_by_tenant = {
            "T1": [{"name": "R1"}, {"name": "R2"}],
            "T2": [{"name": "R1"}, {"name": "R2"}],
        }

        result = OpenWebuiProvisioner._build_desired_groups(tenants, roles_by_tenant)

        assert result == {
            f"{AIHUB_GROUP_PREFIX}T1:R1",
            f"{AIHUB_GROUP_PREFIX}T1:R2",
            f"{AIHUB_GROUP_PREFIX}T2:R1",
            f"{AIHUB_GROUP_PREFIX}T2:R2",
        }

    def test_build_desired_groups_empty_tenants(self) -> None:
        result = OpenWebuiProvisioner._build_desired_groups([], {})
        assert result == set()

    def test_build_desired_groups_empty_roles(self) -> None:
        tenants = [{"name": "T1"}]
        roles_by_tenant = {"T1": []}

        result = OpenWebuiProvisioner._build_desired_groups(tenants, roles_by_tenant)

        assert result == set()

    def test_group_name_format(self) -> None:
        tenants = [{"name": "Default Organization"}]
        roles_by_tenant = {"Default Organization": [{"name": "AIHubUser"}]}

        result = OpenWebuiProvisioner._build_desired_groups(tenants, roles_by_tenant)

        group = next(iter(result))
        assert group.startswith(AIHUB_GROUP_PREFIX)
        assert "Default Organization" in group
        assert "AIHubUser" in group
        assert group == "aihub:Default Organization:AIHubUser"


class TestBuildUserIdMapping:
    def test_user_id_mapping_by_email(self) -> None:
        aihub_users = [{"id": "ah-1", "email": "alice@example.com"}]
        owui_users = [{"id": "owui-1", "userName": "alice@example.com"}]

        result = OpenWebuiProvisioner._build_user_id_mapping(aihub_users, owui_users)

        assert result == {"ah-1": "owui-1"}

    def test_user_id_mapping_skips_unknown_users(self) -> None:
        aihub_users = [
            {"id": "ah-1", "email": "alice@example.com"},
            {"id": "ah-2", "email": "bob@example.com"},
        ]
        owui_users = [{"id": "owui-1", "userName": "alice@example.com"}]

        result = OpenWebuiProvisioner._build_user_id_mapping(aihub_users, owui_users)

        assert result == {"ah-1": "owui-1"}
        assert "ah-2" not in result


class TestSyncGroupsOrchestration:
    @pytest.mark.asyncio
    async def test_sync_creates_missing_groups(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.TenantEntity") as mock_tenant,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.RoleEntity") as mock_role,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserTenantRoleEntity"),
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserEntity") as mock_user,
            patch.object(provisioner._client, "list_groups") as mock_list_groups,
            patch.object(provisioner._client, "create_group") as mock_create,
            patch.object(provisioner._client, "delete_group"),
            patch.object(provisioner._client, "list_users", return_value=[]),
            patch.object(provisioner._client, "update_group_members"),
        ):
            tenant = MagicMock()
            tenant.name = "T1"
            tenant.id = "tid-1"
            tenant.access_rules = []
            mock_tenant.objects.return_value = [tenant]

            role = MagicMock()
            role.name = "R1"
            role.access_rules = []
            mock_role.get_roles_for_tenant.return_value = [role]

            mock_user.objects.return_value = []

            # First call returns no existing groups, second call returns the created group
            mock_list_groups.side_effect = [
                [],
                [{"displayName": "aihub:T1:R1", "id": "grp-1"}],
            ]
            mock_create.return_value = {"id": "grp-1"}

            await provisioner._sync_groups(mock_client)

            mock_create.assert_called_once_with(mock_client, "aihub:T1:R1", "AI-Hub managed group: aihub:T1:R1")

    @pytest.mark.asyncio
    async def test_sync_deletes_orphaned_groups(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.TenantEntity") as mock_tenant,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.RoleEntity") as mock_role,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserTenantRoleEntity"),
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserEntity") as mock_user,
            patch.object(provisioner._client, "list_groups") as mock_list_groups,
            patch.object(provisioner._client, "create_group"),
            patch.object(provisioner._client, "delete_group") as mock_delete,
            patch.object(provisioner._client, "list_users", return_value=[]),
            patch.object(provisioner._client, "update_group_members"),
        ):
            mock_tenant.objects.return_value = []
            mock_role.get_roles_for_tenant.return_value = []
            mock_user.objects.return_value = []

            orphaned_group = {"displayName": "aihub:OldTenant:OldRole", "id": "grp-orphan"}
            mock_list_groups.side_effect = [
                [orphaned_group],
                [],
            ]

            await provisioner._sync_groups(mock_client)

            mock_delete.assert_called_once_with(mock_client, "grp-orphan")

    @pytest.mark.asyncio
    async def test_sync_ignores_non_aihub_groups(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.TenantEntity") as mock_tenant,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.RoleEntity") as mock_role,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserTenantRoleEntity"),
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserEntity") as mock_user,
            patch.object(provisioner._client, "list_groups") as mock_list_groups,
            patch.object(provisioner._client, "create_group"),
            patch.object(provisioner._client, "delete_group") as mock_delete,
            patch.object(provisioner._client, "list_users", return_value=[]),
            patch.object(provisioner._client, "update_group_members"),
        ):
            mock_tenant.objects.return_value = []
            mock_role.get_roles_for_tenant.return_value = []
            mock_user.objects.return_value = []

            non_aihub = {"displayName": "custom-group", "id": "grp-custom"}
            mock_list_groups.side_effect = [
                [non_aihub],
                [non_aihub],
            ]

            await provisioner._sync_groups(mock_client)

            mock_delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_updates_group_membership(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.TenantEntity") as mock_tenant,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.RoleEntity") as mock_role,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserTenantRoleEntity") as mock_utr,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserEntity") as mock_user,
            patch.object(provisioner._client, "list_groups") as mock_list_groups,
            patch.object(provisioner._client, "create_group"),
            patch.object(provisioner._client, "delete_group"),
            patch.object(provisioner._client, "list_users") as mock_list_users,
            patch.object(provisioner._client, "update_group_members") as mock_update_members,
        ):
            tenant = MagicMock()
            tenant.name = "T1"
            tenant.id = "tid-1"
            tenant.access_rules = []
            mock_tenant.objects.return_value = [tenant]

            role = MagicMock()
            role.name = "R1"
            role.access_rules = []
            mock_role.get_roles_for_tenant.return_value = [role]

            user_entity = MagicMock()
            user_entity.id = "ah-user-1"
            user_entity.email = "alice@example.com"
            mock_user.objects.return_value = [user_entity]

            utr = MagicMock()
            utr.user_id = "ah-user-1"
            mock_utr.objects.return_value = [utr]

            group = {"displayName": "aihub:T1:R1", "id": "grp-1"}
            mock_list_groups.side_effect = [[group], [group]]

            mock_list_users.return_value = [{"id": "owui-1", "userName": "alice@example.com"}]

            await provisioner._sync_groups(mock_client)

            mock_update_members.assert_called_once_with(mock_client, "grp-1", ["owui-1"])

    @pytest.mark.asyncio
    async def test_sync_idempotent(self, provisioner: OpenWebuiProvisioner) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)

        with (
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.TenantEntity") as mock_tenant,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.RoleEntity") as mock_role,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserTenantRoleEntity") as mock_utr,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserEntity") as mock_user,
            patch.object(provisioner._client, "list_groups") as mock_list_groups,
            patch.object(provisioner._client, "create_group") as mock_create,
            patch.object(provisioner._client, "delete_group") as mock_delete,
            patch.object(provisioner._client, "list_users", return_value=[]),
            patch.object(provisioner._client, "update_group_members"),
        ):
            tenant = MagicMock()
            tenant.name = "T1"
            tenant.id = "tid-1"
            tenant.access_rules = []
            mock_tenant.objects.return_value = [tenant]

            role = MagicMock()
            role.name = "R1"
            role.access_rules = []
            mock_role.get_roles_for_tenant.return_value = [role]

            mock_user.objects.return_value = []
            mock_utr.objects.return_value = []

            existing_group = {"displayName": "aihub:T1:R1", "id": "grp-1"}
            mock_list_groups.side_effect = [[existing_group], [existing_group]]

            await provisioner._sync_groups(mock_client)

            mock_create.assert_not_called()
            mock_delete.assert_not_called()
