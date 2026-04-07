from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from scim2_models import Group

from swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner import OpenWebuiProvisioner


class TestBuildDesiredGroups:
    def test_cross_product(self):
        tenants = [{"name": "T1", "id": "t1", "access_rules": []}, {"name": "T2", "id": "t2", "access_rules": []}]
        roles_by_tenant = {
            "T1": [{"name": "R1", "access_rules": []}, {"name": "R2", "access_rules": []}],
            "T2": [{"name": "R1", "access_rules": []}],
        }
        result = OpenWebuiProvisioner._build_desired_groups(tenants, roles_by_tenant)
        assert result == {"aihub:T1:R1", "aihub:T1:R2", "aihub:T2:R1"}

    def test_empty_tenants(self):
        result = OpenWebuiProvisioner._build_desired_groups([], {})
        assert result == set()

    def test_no_roles_for_tenant(self):
        tenants = [{"name": "T1", "id": "t1", "access_rules": []}]
        result = OpenWebuiProvisioner._build_desired_groups(tenants, {})
        assert result == set()


class TestBuildUserIdMapping:
    def test_maps_by_email(self):
        aihub_users = [
            {"id": "uid-1", "email": "alice@example.com"},
            {"id": "uid-2", "email": "bob@example.com"},
        ]
        owui_user_1 = MagicMock(spec=["user_name", "id"])
        owui_user_1.user_name = "alice@example.com"
        owui_user_1.id = "owui-1"

        owui_user_2 = MagicMock(spec=["user_name", "id"])
        owui_user_2.user_name = "bob@example.com"
        owui_user_2.id = "owui-2"

        result = OpenWebuiProvisioner._build_user_id_mapping(aihub_users, [owui_user_1, owui_user_2])
        assert result == {"uid-1": "owui-1", "uid-2": "owui-2"}

    def test_missing_owui_user(self):
        aihub_users = [{"id": "uid-1", "email": "alice@example.com"}]
        result = OpenWebuiProvisioner._build_user_id_mapping(aihub_users, [])
        assert result == {}


class TestSyncGroups:
    @pytest.mark.asyncio
    async def test_creates_missing_groups(self, provisioner: OpenWebuiProvisioner):
        with (
            patch.object(provisioner, "_openwebui") as mock_client,
            patch("swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.TenantEntity") as mock_tenant_cls,
            patch("swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.RoleEntity") as mock_role_cls,
            patch("swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.UserEntity") as mock_user_cls,
            patch("swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.UserTenantRoleEntity"),
        ):
            tenant = MagicMock()
            tenant.name = "TestTenant"
            tenant.id = "t1"
            tenant.access_rules = []
            mock_tenant_cls.objects.return_value = [tenant]
            mock_tenant_cls.get_default_tenant.return_value = tenant

            role = MagicMock()
            role.name = "TestRole"
            role.access_rules = []
            mock_role_cls.get_roles_for_tenant.return_value = [role]

            mock_client.list_groups = AsyncMock(return_value=[])
            created_group = Group(id="g1", display_name="aihub:TestTenant:TestRole")
            mock_client.create_group = AsyncMock(return_value=created_group)
            mock_client.list_users = AsyncMock(return_value=[])
            mock_client.update_group_members = AsyncMock()

            mock_user_cls.objects.return_value = []
            # _get_active_user_ids calls .objects(__raw__=...).only("id") — mock the chain
            mock_qs = MagicMock()
            mock_qs.only.return_value = []
            mock_user_cls.objects.return_value = mock_qs

            await provisioner._sync_groups()

            mock_client.create_group.assert_called_once_with("aihub:TestTenant:TestRole")

    @pytest.mark.asyncio
    async def test_deletes_orphaned_groups(self, provisioner: OpenWebuiProvisioner):
        with (
            patch.object(provisioner, "_openwebui") as mock_client,
            patch("swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.TenantEntity") as mock_tenant_cls,
            patch("swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.RoleEntity") as mock_role_cls,
            patch("swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.UserEntity") as mock_user_cls,
            patch("swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.UserTenantRoleEntity"),
        ):
            mock_tenant_cls.objects.return_value = []
            mock_tenant_cls.get_default_tenant.return_value = None

            orphaned_group = Group(id="g-orphan", display_name="aihub:OldTenant:OldRole")
            non_aihub_group = Group(id="g-other", display_name="other-group")
            mock_client.list_groups = AsyncMock(return_value=[orphaned_group, non_aihub_group])
            mock_client.delete_group = AsyncMock()
            mock_client.list_users = AsyncMock(return_value=[])

            mock_user_cls.objects.return_value = []
            mock_role_cls.get_roles_for_tenant.return_value = []

            await provisioner._sync_groups()

            mock_client.delete_group.assert_called_once_with("g-orphan")
