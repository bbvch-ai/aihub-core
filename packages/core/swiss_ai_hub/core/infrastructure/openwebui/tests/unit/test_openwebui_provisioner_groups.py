from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from scim2_models import Group, User

from swiss_ai_hub.core.auth.realm_roles import SYS_ADMIN_ROLE
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner import (
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
    def test_single_tenant_single_role(self) -> None:
        tenants = [{"name": "TenantA"}]
        roles_by_tenant = {"TenantA": [{"name": "RoleA"}]}

        result = OpenWebuiProvisioner._build_desired_groups(tenants, roles_by_tenant)

        assert result == {f"{AIHUB_GROUP_PREFIX}TenantA:RoleA", f"{AIHUB_GROUP_PREFIX}TenantA:{SYS_ADMIN_ROLE}"}

    def test_cross_product(self) -> None:
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
            f"{AIHUB_GROUP_PREFIX}T1:{SYS_ADMIN_ROLE}",
            f"{AIHUB_GROUP_PREFIX}T2:{SYS_ADMIN_ROLE}",
        }

    def test_empty_tenants(self) -> None:
        result = OpenWebuiProvisioner._build_desired_groups([], {})
        assert result == set()

    def test_no_roles_for_tenant_still_gets_sys_admin_group(self) -> None:
        """A sysadmin needs no tenant role, so even a tenant without roles has a group for them."""
        tenants = [{"name": "T1"}]
        result = OpenWebuiProvisioner._build_desired_groups(tenants, {})
        assert result == {f"{AIHUB_GROUP_PREFIX}T1:{SYS_ADMIN_ROLE}"}


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

    def test_missing_owui_user(self) -> None:
        aihub_users = [{"id": "uid-1", "email": "alice@example.com"}]
        result = OpenWebuiProvisioner._build_user_id_mapping(aihub_users, [])
        assert result == {}

    def test_user_id_mapping_falls_back_to_external_id_after_email_change(self) -> None:
        """OpenWebUI keeps the email the account was created with, so only the Keycloak sub still matches."""
        aihub_users = [{"id": "kc-sub-1", "email": "alice.new@example.com"}]
        owui_user = _user("alice.old@example.com", "owui-1")
        owui_user.external_id = "kc-sub-1"

        result = OpenWebuiProvisioner._build_user_id_mapping(aihub_users, [owui_user])

        assert result == {"kc-sub-1": "owui-1"}


class TestSyncGroupsOrchestration:
    @pytest.mark.asyncio
    async def test_sync_creates_missing_groups(self, provisioner: OpenWebuiProvisioner) -> None:
        with (
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.TenantMetadataEntity",
                new_callable=AsyncMock,
            ) as mock_tenant,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.RoleEntity", new_callable=AsyncMock
            ) as mock_role,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.UserTenantRoleEntity",
                new_callable=AsyncMock,
            ),
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.KeycloakAdminService"
            ) as mock_keycloak,
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
            mock_tenant.get_all_metadata.return_value = [tenant]
            mock_tenant.get_startup_tenant_metadata.return_value = tenant

            role = MagicMock()
            role.name = "R1"
            role.access_rules = []
            mock_role.get_roles_for_tenant.return_value = [role]

            mock_keycloak.get_user_ids_with_active_tenant = AsyncMock(return_value=set())
            mock_keycloak.get_all_users = AsyncMock(return_value=[])
            mock_keycloak.get_user_ids_with_realm_role = AsyncMock(return_value=set())

            mock_list_groups.return_value = []
            mock_create.side_effect = lambda name, scim: _group(name, f"grp-{name}")

            await provisioner._sync_groups()

            assert {call.args[0] for call in mock_create.call_args_list} == {
                "aihub:T1:R1",
                f"aihub:T1:{SYS_ADMIN_ROLE}",
            }

    @pytest.mark.asyncio
    async def test_sync_deletes_orphaned_groups(self, provisioner: OpenWebuiProvisioner) -> None:
        with (
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.TenantMetadataEntity",
                new_callable=AsyncMock,
            ) as mock_tenant,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.RoleEntity", new_callable=AsyncMock
            ) as mock_role,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.UserTenantRoleEntity",
                new_callable=AsyncMock,
            ),
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.KeycloakAdminService"
            ) as mock_keycloak,
            patch.object(provisioner._openwebui, "list_groups") as mock_list_groups,
            patch.object(provisioner._openwebui, "create_group"),
            patch.object(provisioner._openwebui, "delete_group") as mock_delete,
            patch.object(provisioner._openwebui, "list_users", return_value=[]),
            patch.object(provisioner._openwebui, "update_group_members"),
        ):
            mock_tenant.get_all_metadata.return_value = []
            mock_tenant.get_startup_tenant_metadata.return_value = None
            mock_role.get_roles_for_tenant.return_value = []
            mock_keycloak.get_user_ids_with_active_tenant = AsyncMock(return_value=set())
            mock_keycloak.get_all_users = AsyncMock(return_value=[])
            mock_keycloak.get_user_ids_with_realm_role = AsyncMock(return_value=set())

            mock_list_groups.return_value = [_group("aihub:OldTenant:OldRole", "grp-orphan")]

            await provisioner._sync_groups()

            mock_delete.assert_called_once_with("grp-orphan", scim=ANY)

    @pytest.mark.asyncio
    async def test_sync_ignores_non_aihub_groups(self, provisioner: OpenWebuiProvisioner) -> None:
        with (
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.TenantMetadataEntity",
                new_callable=AsyncMock,
            ) as mock_tenant,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.RoleEntity", new_callable=AsyncMock
            ) as mock_role,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.UserTenantRoleEntity",
                new_callable=AsyncMock,
            ),
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.KeycloakAdminService"
            ) as mock_keycloak,
            patch.object(provisioner._openwebui, "list_groups") as mock_list_groups,
            patch.object(provisioner._openwebui, "create_group"),
            patch.object(provisioner._openwebui, "delete_group") as mock_delete,
            patch.object(provisioner._openwebui, "list_users", return_value=[]),
            patch.object(provisioner._openwebui, "update_group_members"),
        ):
            mock_tenant.get_all_metadata.return_value = []
            mock_tenant.get_startup_tenant_metadata.return_value = None
            mock_role.get_roles_for_tenant.return_value = []
            mock_keycloak.get_user_ids_with_active_tenant = AsyncMock(return_value=set())
            mock_keycloak.get_all_users = AsyncMock(return_value=[])
            mock_keycloak.get_user_ids_with_realm_role = AsyncMock(return_value=set())

            mock_list_groups.return_value = [_group("custom-group", "grp-custom")]

            await provisioner._sync_groups()

            mock_delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_updates_group_membership(
        self, provisioner: OpenWebuiProvisioner, recorded_accounts: MagicMock
    ) -> None:
        with (
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.TenantMetadataEntity",
                new_callable=AsyncMock,
            ) as mock_tenant,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.RoleEntity", new_callable=AsyncMock
            ) as mock_role,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.UserTenantRoleEntity",
                new_callable=AsyncMock,
            ) as mock_utr,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.KeycloakAdminService"
            ) as mock_keycloak,
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
            mock_tenant.get_all_metadata.return_value = [tenant]
            mock_tenant.get_startup_tenant_metadata.return_value = tenant

            role = MagicMock()
            role.name = "R1"
            role.access_rules = []
            mock_role.get_roles_for_tenant.return_value = [role]

            mock_keycloak.get_user_ids_with_active_tenant = AsyncMock(return_value={"ah-user-1"})
            kc_user = MagicMock()
            kc_user.id = "ah-user-1"
            kc_user.email = "alice@example.com"
            mock_keycloak.get_all_users = AsyncMock(return_value=[kc_user])
            mock_keycloak.get_user_ids_with_realm_role = AsyncMock(return_value=set())

            mock_utr.get_user_ids_with_role.return_value = ["ah-user-1"]

            mock_list_groups.return_value = [
                _group("aihub:T1:R1", "grp-1"),
                _group(f"aihub:T1:{SYS_ADMIN_ROLE}", "grp-sys"),
            ]
            mock_list_users.return_value = [_user("alice@example.com", "owui-1")]

            await provisioner._sync_groups()

            mock_update_members.assert_any_call("grp-1", ["owui-1"], scim=ANY)
            mock_update_members.assert_any_call("grp-sys", [], scim=ANY)
            recorded_accounts.record_all.assert_called_once_with({"ah-user-1": "owui-1"})

    @pytest.mark.asyncio
    async def test_sync_excludes_user_with_different_active_tenant(self, provisioner: OpenWebuiProvisioner) -> None:
        """User has role in tenant but active_tenant_id points to a different tenant -- excluded from group."""
        with (
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.TenantMetadataEntity",
                new_callable=AsyncMock,
            ) as mock_tenant,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.RoleEntity", new_callable=AsyncMock
            ) as mock_role,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.UserTenantRoleEntity",
                new_callable=AsyncMock,
            ) as mock_utr,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.KeycloakAdminService"
            ) as mock_keycloak,
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
            mock_tenant.get_all_metadata.return_value = [tenant]
            mock_tenant.get_startup_tenant_metadata.return_value = tenant

            role = MagicMock()
            role.name = "R1"
            role.access_rules = []
            mock_role.get_roles_for_tenant.return_value = [role]

            mock_keycloak.get_user_ids_with_active_tenant = AsyncMock(return_value=set())
            mock_keycloak.get_all_users = AsyncMock(return_value=[])
            mock_keycloak.get_user_ids_with_realm_role = AsyncMock(return_value=set())

            mock_utr.get_user_ids_with_role.return_value = ["ah-user-1"]

            mock_list_groups.return_value = [_group("aihub:T1:R1", "grp-1")]
            mock_list_users.return_value = [_user("alice@example.com", "owui-1")]

            await provisioner._sync_groups()

            mock_update_members.assert_any_call("grp-1", [], scim=ANY)

    @pytest.mark.asyncio
    async def test_sync_idempotent(self, provisioner: OpenWebuiProvisioner) -> None:
        with (
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.TenantMetadataEntity",
                new_callable=AsyncMock,
            ) as mock_tenant,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.RoleEntity", new_callable=AsyncMock
            ) as mock_role,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.UserTenantRoleEntity",
                new_callable=AsyncMock,
            ) as mock_utr,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.KeycloakAdminService"
            ) as mock_keycloak,
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
            mock_tenant.get_all_metadata.return_value = [tenant]
            mock_tenant.get_startup_tenant_metadata.return_value = tenant

            role = MagicMock()
            role.name = "R1"
            role.access_rules = []
            mock_role.get_roles_for_tenant.return_value = [role]

            mock_keycloak.get_user_ids_with_active_tenant = AsyncMock(return_value=set())
            mock_keycloak.get_all_users = AsyncMock(return_value=[])
            mock_keycloak.get_user_ids_with_realm_role = AsyncMock(return_value=set())
            mock_utr.get_user_ids_with_role.return_value = []

            mock_list_groups.return_value = [
                _group("aihub:T1:R1", "grp-1"),
                _group(f"aihub:T1:{SYS_ADMIN_ROLE}", "grp-sys"),
            ]

            await provisioner._sync_groups()

            mock_create.assert_not_called()
            mock_delete.assert_not_called()


class TestSyncGroupsLocking:
    @pytest.mark.asyncio
    async def test_group_sync_uses_dedicated_blocking_lock(
        self, provisioner: OpenWebuiProvisioner, mock_redis: MagicMock
    ) -> None:
        with (
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.TenantMetadataEntity",
                new_callable=AsyncMock,
            ) as mock_tenant,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.RoleEntity", new_callable=AsyncMock
            ) as mock_role,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.UserTenantRoleEntity",
                new_callable=AsyncMock,
            ),
            patch("swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.KeycloakAdminService") as mock_kc,
            patch.object(provisioner._openwebui, "list_groups", return_value=[]),
            patch.object(provisioner._openwebui, "list_users", return_value=[]),
        ):
            mock_tenant.get_all_metadata.return_value = []
            mock_role.get_roles_for_tenant.return_value = []
            mock_kc.get_all_users = AsyncMock(return_value=[])
            mock_kc.get_user_ids_with_realm_role = AsyncMock(return_value=set())

            await provisioner._sync_groups()

        lock_keys = [call.args[0] for call in mock_redis.lock.call_args_list]
        assert "openwebui:sync:groups" in lock_keys

    @pytest.mark.asyncio
    async def test_group_sync_skipped_when_lock_not_acquired(
        self, provisioner: OpenWebuiProvisioner, mock_redis: MagicMock
    ) -> None:
        mock_redis.lock.return_value.acquire = AsyncMock(return_value=False)

        with patch.object(provisioner._openwebui, "list_groups") as mock_list_groups:
            await provisioner._sync_groups()

        # No group reconciliation happens when the serialization lock is contended.
        mock_list_groups.assert_not_called()


class TestSysAdminGroupMembership:
    """A sysadmin uses every agent without a tenant role, so the tenant they act in gives them a group of their own."""

    @staticmethod
    def _tenant(name: str, tenant_id: str) -> MagicMock:
        tenant = MagicMock()
        tenant.name = name
        tenant.id = tenant_id
        tenant.access_rules = []
        return tenant

    @pytest.mark.asyncio
    async def test_sys_admin_without_role_joins_only_their_active_tenants_group(
        self, provisioner: OpenWebuiProvisioner
    ) -> None:
        active_users_by_tenant = {"tid-1": {"kc-sys", "kc-plain"}, "tid-2": set()}
        with (
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.TenantMetadataEntity",
                new_callable=AsyncMock,
            ) as mock_tenant,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.RoleEntity", new_callable=AsyncMock
            ) as mock_role,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.UserTenantRoleEntity",
                new_callable=AsyncMock,
            ) as mock_utr,
            patch(
                "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner.KeycloakAdminService"
            ) as mock_keycloak,
            patch.object(
                provisioner._openwebui,
                "list_groups",
                return_value=[
                    _group(f"aihub:T1:{SYS_ADMIN_ROLE}", "grp-sys-1"),
                    _group(f"aihub:T2:{SYS_ADMIN_ROLE}", "grp-sys-2"),
                ],
            ),
            patch.object(
                provisioner._openwebui,
                "list_users",
                return_value=[_user("sys@example.com", "owui-sys"), _user("plain@example.com", "owui-plain")],
            ),
            patch.object(provisioner._openwebui, "update_group_members") as mock_update_members,
        ):
            mock_tenant.get_all_metadata.return_value = [self._tenant("T1", "tid-1"), self._tenant("T2", "tid-2")]
            mock_role.get_roles_for_tenant.return_value = []
            mock_utr.get_user_ids_with_role.return_value = []
            mock_keycloak.get_user_ids_with_active_tenant = AsyncMock(side_effect=active_users_by_tenant.get)
            mock_keycloak.get_user_ids_with_realm_role = AsyncMock(return_value={"kc-sys"})
            sys_admin, plain_user = MagicMock(), MagicMock()
            sys_admin.id, sys_admin.email = "kc-sys", "sys@example.com"
            plain_user.id, plain_user.email = "kc-plain", "plain@example.com"
            mock_keycloak.get_all_users = AsyncMock(return_value=[sys_admin, plain_user])

            await provisioner._sync_groups()

            mock_keycloak.get_user_ids_with_realm_role.assert_awaited_once_with(SYS_ADMIN_ROLE)
            assert {call.args[0]: call.args[1] for call in mock_update_members.call_args_list} == {
                "grp-sys-1": ["owui-sys"],
                "grp-sys-2": [],
            }
