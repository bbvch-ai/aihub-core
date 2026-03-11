from unittest.mock import MagicMock, patch

import pytest
from scim2_models import Group, User

from aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner import (
    AIHUB_GROUP_PREFIX,
    OpenWebuiProvisioner,
)


def _group(display_name: str, group_id: str) -> Group:
    g = Group(display_name=display_name)
    g.id = group_id
    return g


def _user(user_name: str, user_id: str) -> User:
    u = User(user_name=user_name)
    u.id = user_id
    return u


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


class TestBuildUserIdMapping:
    def test_user_id_mapping_by_email(self) -> None:
        aihub_users = [{"id": "ah-1", "email": "alice@example.com"}]
        owui_users = [_user("alice@example.com", "owui-1")]

        result = OpenWebuiProvisioner._build_user_id_mapping(aihub_users, owui_users)

        assert result == {"ah-1": "owui-1"}

    def test_user_id_mapping_skips_unknown_users(self) -> None:
        aihub_users = [
            {"id": "ah-1", "email": "alice@example.com"},
            {"id": "ah-2", "email": "bob@example.com"},
        ]
        owui_users = [_user("alice@example.com", "owui-1")]

        result = OpenWebuiProvisioner._build_user_id_mapping(aihub_users, owui_users)

        assert result == {"ah-1": "owui-1"}
        assert "ah-2" not in result


class TestSyncGroupsOrchestration:
    @pytest.mark.asyncio
    async def test_sync_creates_missing_groups(self, provisioner: OpenWebuiProvisioner) -> None:
        with (
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.TenantEntity") as mock_tenant,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.RoleEntity") as mock_role,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserTenantRoleEntity"),
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserEntity") as mock_user,
            patch.object(provisioner._openwebui, "list_groups") as mock_list_groups,
            patch.object(provisioner._openwebui, "create_group") as mock_create,
            patch.object(provisioner._openwebui, "delete_group"),
            patch.object(provisioner._openwebui, "list_users", return_value=[]),
            patch.object(provisioner._openwebui, "update_group_members"),
        ):
            tenant = MagicMock()
            tenant.name = "T1"
            tenant.id = "tid-1"
            tenant.access_rules = []
            mock_tenant.objects.return_value = [tenant]
            mock_tenant.get_default_tenant.return_value = tenant

            role = MagicMock()
            role.name = "R1"
            role.access_rules = []
            mock_role.get_roles_for_tenant.return_value = [role]

            active_queryset = MagicMock()
            active_queryset.only.return_value = []

            def user_objects_router(*args, **kwargs):
                if "__raw__" in kwargs or "active_tenant_id" in kwargs:
                    return active_queryset
                return []

            mock_user.objects.side_effect = user_objects_router

            mock_list_groups.return_value = []
            mock_create.return_value = _group("aihub:T1:R1", "grp-1")

            await provisioner._sync_groups()

            mock_create.assert_called_once_with("aihub:T1:R1")

    @pytest.mark.asyncio
    async def test_sync_deletes_orphaned_groups(self, provisioner: OpenWebuiProvisioner) -> None:
        with (
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.TenantEntity") as mock_tenant,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.RoleEntity") as mock_role,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserTenantRoleEntity"),
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserEntity") as mock_user,
            patch.object(provisioner._openwebui, "list_groups") as mock_list_groups,
            patch.object(provisioner._openwebui, "create_group"),
            patch.object(provisioner._openwebui, "delete_group") as mock_delete,
            patch.object(provisioner._openwebui, "list_users", return_value=[]),
            patch.object(provisioner._openwebui, "update_group_members"),
        ):
            mock_tenant.objects.return_value = []
            mock_tenant.get_default_tenant.return_value = None
            mock_role.get_roles_for_tenant.return_value = []
            mock_user.objects.return_value = []

            mock_list_groups.return_value = [_group("aihub:OldTenant:OldRole", "grp-orphan")]

            await provisioner._sync_groups()

            mock_delete.assert_called_once_with("grp-orphan")

    @pytest.mark.asyncio
    async def test_sync_ignores_non_aihub_groups(self, provisioner: OpenWebuiProvisioner) -> None:
        with (
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.TenantEntity") as mock_tenant,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.RoleEntity") as mock_role,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserTenantRoleEntity"),
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserEntity") as mock_user,
            patch.object(provisioner._openwebui, "list_groups") as mock_list_groups,
            patch.object(provisioner._openwebui, "create_group"),
            patch.object(provisioner._openwebui, "delete_group") as mock_delete,
            patch.object(provisioner._openwebui, "list_users", return_value=[]),
            patch.object(provisioner._openwebui, "update_group_members"),
        ):
            mock_tenant.objects.return_value = []
            mock_tenant.get_default_tenant.return_value = None
            mock_role.get_roles_for_tenant.return_value = []
            mock_user.objects.return_value = []

            mock_list_groups.return_value = [_group("custom-group", "grp-custom")]

            await provisioner._sync_groups()

            mock_delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_updates_group_membership(self, provisioner: OpenWebuiProvisioner) -> None:
        with (
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.TenantEntity") as mock_tenant,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.RoleEntity") as mock_role,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserTenantRoleEntity") as mock_utr,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserEntity") as mock_user,
            patch.object(provisioner._openwebui, "list_groups") as mock_list_groups,
            patch.object(provisioner._openwebui, "create_group"),
            patch.object(provisioner._openwebui, "delete_group"),
            patch.object(provisioner._openwebui, "list_users") as mock_list_users,
            patch.object(provisioner._openwebui, "update_group_members") as mock_update_members,
        ):
            tenant = MagicMock()
            tenant.name = "T1"
            tenant.id = "tid-1"
            tenant.access_rules = []
            mock_tenant.objects.return_value = [tenant]

            default_tenant = MagicMock()
            default_tenant.id = "tid-1"
            mock_tenant.get_default_tenant.return_value = default_tenant

            role = MagicMock()
            role.name = "R1"
            role.access_rules = []
            mock_role.get_roles_for_tenant.return_value = [role]

            user_entity = MagicMock()
            user_entity.id = "ah-user-1"
            user_entity.email = "alice@example.com"

            active_user = MagicMock()
            active_user.id = "ah-user-1"
            active_queryset = MagicMock()
            active_queryset.only.return_value = [active_user]

            def user_objects_router(*args, **kwargs):
                if "__raw__" in kwargs or "active_tenant_id" in kwargs:
                    return active_queryset
                return [user_entity]

            mock_user.objects.side_effect = user_objects_router

            utr = MagicMock()
            utr.user_id = "ah-user-1"
            mock_utr.objects.return_value = [utr]

            mock_list_groups.return_value = [_group("aihub:T1:R1", "grp-1")]
            mock_list_users.return_value = [_user("alice@example.com", "owui-1")]

            await provisioner._sync_groups()

            mock_update_members.assert_called_once_with("grp-1", ["owui-1"])

    @pytest.mark.asyncio
    async def test_sync_excludes_user_with_different_active_tenant(self, provisioner: OpenWebuiProvisioner) -> None:
        """User has role in tenant but active_tenant_id points to a different tenant — excluded from group."""
        with (
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.TenantEntity") as mock_tenant,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.RoleEntity") as mock_role,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserTenantRoleEntity") as mock_utr,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserEntity") as mock_user,
            patch.object(provisioner._openwebui, "list_groups") as mock_list_groups,
            patch.object(provisioner._openwebui, "create_group"),
            patch.object(provisioner._openwebui, "delete_group"),
            patch.object(provisioner._openwebui, "list_users") as mock_list_users,
            patch.object(provisioner._openwebui, "update_group_members") as mock_update_members,
        ):
            tenant = MagicMock()
            tenant.name = "T1"
            tenant.id = "tid-1"
            tenant.access_rules = []
            mock_tenant.objects.return_value = [tenant]

            default_tenant = MagicMock()
            default_tenant.id = "tid-1"
            mock_tenant.get_default_tenant.return_value = default_tenant

            role = MagicMock()
            role.name = "R1"
            role.access_rules = []
            mock_role.get_roles_for_tenant.return_value = [role]

            user_entity = MagicMock()
            user_entity.id = "ah-user-1"
            user_entity.email = "alice@example.com"

            # User's active tenant is tid-2, not tid-1 — empty active set for tid-1
            active_queryset = MagicMock()
            active_queryset.only.return_value = []

            def user_objects_router(*args, **kwargs):
                if "__raw__" in kwargs or "active_tenant_id" in kwargs:
                    return active_queryset
                return [user_entity]

            mock_user.objects.side_effect = user_objects_router

            utr = MagicMock()
            utr.user_id = "ah-user-1"
            mock_utr.objects.return_value = [utr]

            mock_list_groups.return_value = [_group("aihub:T1:R1", "grp-1")]
            mock_list_users.return_value = [_user("alice@example.com", "owui-1")]

            await provisioner._sync_groups()

            mock_update_members.assert_called_once_with("grp-1", [])

    @pytest.mark.asyncio
    async def test_sync_includes_null_active_tenant_in_default_tenant_group(
        self, provisioner: OpenWebuiProvisioner
    ) -> None:
        """User with null active_tenant_id is included in the default tenant's group."""
        with (
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.TenantEntity") as mock_tenant,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.RoleEntity") as mock_role,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserTenantRoleEntity") as mock_utr,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserEntity") as mock_user,
            patch.object(provisioner._openwebui, "list_groups") as mock_list_groups,
            patch.object(provisioner._openwebui, "create_group"),
            patch.object(provisioner._openwebui, "delete_group"),
            patch.object(provisioner._openwebui, "list_users") as mock_list_users,
            patch.object(provisioner._openwebui, "update_group_members") as mock_update_members,
        ):
            tenant = MagicMock()
            tenant.name = "DefaultOrg"
            tenant.id = "tid-default"
            tenant.access_rules = []
            mock_tenant.objects.return_value = [tenant]

            default_tenant = MagicMock()
            default_tenant.id = "tid-default"
            mock_tenant.get_default_tenant.return_value = default_tenant

            role = MagicMock()
            role.name = "R1"
            role.access_rules = []
            mock_role.get_roles_for_tenant.return_value = [role]

            user_entity = MagicMock()
            user_entity.id = "ah-user-1"
            user_entity.email = "alice@example.com"

            # User with null active_tenant_id matches __raw__ $or query for default tenant
            active_user = MagicMock()
            active_user.id = "ah-user-1"
            active_queryset = MagicMock()
            active_queryset.only.return_value = [active_user]

            def user_objects_router(*args, **kwargs):
                if "__raw__" in kwargs:
                    return active_queryset
                if "active_tenant_id" in kwargs:
                    return active_queryset
                return [user_entity]

            mock_user.objects.side_effect = user_objects_router

            utr = MagicMock()
            utr.user_id = "ah-user-1"
            mock_utr.objects.return_value = [utr]

            mock_list_groups.return_value = [_group("aihub:DefaultOrg:R1", "grp-1")]
            mock_list_users.return_value = [_user("alice@example.com", "owui-1")]

            await provisioner._sync_groups()

            # User should be included because __raw__ $or matches null active_tenant_id
            mock_update_members.assert_called_once_with("grp-1", ["owui-1"])
            # Verify the __raw__ query was used (default tenant uses $or)
            raw_calls = [c for c in mock_user.objects.call_args_list if "__raw__" in (c.kwargs or {})]
            assert len(raw_calls) == 1

    @pytest.mark.asyncio
    async def test_sync_idempotent(self, provisioner: OpenWebuiProvisioner) -> None:
        with (
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.TenantEntity") as mock_tenant,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.RoleEntity") as mock_role,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserTenantRoleEntity") as mock_utr,
            patch("aihub_lib.infrastructure.openwebui.OpenWebuiProvisioner.UserEntity") as mock_user,
            patch.object(provisioner._openwebui, "list_groups") as mock_list_groups,
            patch.object(provisioner._openwebui, "create_group") as mock_create,
            patch.object(provisioner._openwebui, "delete_group") as mock_delete,
            patch.object(provisioner._openwebui, "list_users", return_value=[]),
            patch.object(provisioner._openwebui, "update_group_members"),
        ):
            tenant = MagicMock()
            tenant.name = "T1"
            tenant.id = "tid-1"
            tenant.access_rules = []
            mock_tenant.objects.return_value = [tenant]
            mock_tenant.get_default_tenant.return_value = tenant

            role = MagicMock()
            role.name = "R1"
            role.access_rules = []
            mock_role.get_roles_for_tenant.return_value = [role]

            active_queryset = MagicMock()
            active_queryset.only.return_value = []

            def user_objects_router(*args, **kwargs):
                if "__raw__" in kwargs or "active_tenant_id" in kwargs:
                    return active_queryset
                return []

            mock_user.objects.side_effect = user_objects_router
            mock_utr.objects.return_value = []

            mock_list_groups.return_value = [_group("aihub:T1:R1", "grp-1")]

            await provisioner._sync_groups()

            mock_create.assert_not_called()
            mock_delete.assert_not_called()
