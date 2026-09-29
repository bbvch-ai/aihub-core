from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from scim2_models import Group, User

from swiss_ai_hub.core.auth.keycloak.models.keycloak_user import KeycloakUser
from swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner import OpenWebuiProvisioner

_MODULE = "swiss_ai_hub.core.infrastructure.openwebui.openwebui_provisioner"


def _keycloak_user(user_id: str, email: str, *, enabled: bool = True) -> KeycloakUser:
    return KeycloakUser(id=user_id, email=email, first_name="New", last_name="User", enabled=enabled)


def _owui_user(user_name: str, user_id: str) -> User:
    user = User(user_name=user_name)
    user.id = user_id
    return user


def _group(display_name: str, group_id: str) -> Group:
    group = Group(display_name=display_name)
    group.id = group_id
    return group


class TestProvisionMissingAccounts:
    @pytest.mark.asyncio
    async def test_should_create_account_when_user_has_role_but_no_account(
        self, provisioner: OpenWebuiProvisioner
    ) -> None:
        with (
            patch(f"{_MODULE}.UserTenantRoleEntity") as mock_utr,
            patch.object(provisioner._openwebui, "create_user", return_value=_owui_user("a@x", "owui-a")) as create,
        ):
            mock_utr.get_all_user_ids.return_value = {"kc-a"}

            provisioned = await provisioner._provision_missing_accounts([_keycloak_user("kc-a", "a@x")], {})

        create.assert_awaited_once_with(email="a@x", display_name="New User", external_id="kc-a", scim=None)
        assert provisioned == {"kc-a": "owui-a"}

    @pytest.mark.asyncio
    async def test_should_not_create_account_when_user_has_no_role(self, provisioner: OpenWebuiProvisioner) -> None:
        with (
            patch(f"{_MODULE}.UserTenantRoleEntity") as mock_utr,
            patch.object(provisioner._openwebui, "create_user") as create,
        ):
            mock_utr.get_all_user_ids.return_value = set()

            await provisioner._provision_missing_accounts([_keycloak_user("kc-a", "a@x")], {})

        create.assert_not_called()

    @pytest.mark.asyncio
    async def test_should_not_create_account_when_one_exists(self, provisioner: OpenWebuiProvisioner) -> None:
        with (
            patch(f"{_MODULE}.UserTenantRoleEntity") as mock_utr,
            patch.object(provisioner._openwebui, "create_user") as create,
        ):
            mock_utr.get_all_user_ids.return_value = {"kc-a"}

            await provisioner._provision_missing_accounts([_keycloak_user("kc-a", "a@x")], {"kc-a": "owui-a"})

        create.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("user", [_keycloak_user("kc-a", ""), _keycloak_user("kc-a", "a@x", enabled=False)])
    async def test_should_not_create_account_when_user_has_no_email_or_is_disabled(
        self, provisioner: OpenWebuiProvisioner, user: KeycloakUser
    ) -> None:
        with (
            patch(f"{_MODULE}.UserTenantRoleEntity") as mock_utr,
            patch.object(provisioner._openwebui, "create_user") as create,
        ):
            mock_utr.get_all_user_ids.return_value = {"kc-a"}

            await provisioner._provision_missing_accounts([user], {})

        create.assert_not_called()


class TestProvisionedAccountJoinsGroups:
    @pytest.mark.asyncio
    async def test_should_add_provisioned_account_to_role_group(self, provisioner: OpenWebuiProvisioner) -> None:
        """The user's first role triggers a sync before their first chat login created an account."""
        with (
            patch(f"{_MODULE}.TenantMetadataEntity") as mock_tenant,
            patch(f"{_MODULE}.RoleEntity") as mock_role,
            patch(f"{_MODULE}.UserTenantRoleEntity") as mock_utr,
            patch(f"{_MODULE}.KeycloakAdminService") as mock_keycloak,
            patch.object(provisioner._openwebui, "list_groups", return_value=[_group("aihub:T1:R1", "grp-1")]),
            patch.object(provisioner._openwebui, "list_users", return_value=[]),
            patch.object(provisioner._openwebui, "create_user", return_value=_owui_user("a@x", "owui-a")),
            patch.object(provisioner._openwebui, "update_group_members") as update_members,
        ):
            tenant = MagicMock()
            tenant.name, tenant.id, tenant.access_rules = "T1", "tid-1", []
            mock_tenant.objects.return_value = [tenant]
            role = MagicMock()
            role.name, role.access_rules = "R1", []
            mock_role.get_roles_for_tenant.return_value = [role]
            mock_keycloak.get_all_users = AsyncMock(return_value=[_keycloak_user("kc-a", "a@x")])
            mock_keycloak.get_user_ids_with_active_tenant = AsyncMock(return_value={"kc-a"})
            mock_utr.get_all_user_ids.return_value = {"kc-a"}
            mock_utr.objects.return_value = [MagicMock(user_id="kc-a")]

            await provisioner._sync_groups()

        update_members.assert_awaited_once_with("grp-1", ["owui-a"], scim=ANY)
