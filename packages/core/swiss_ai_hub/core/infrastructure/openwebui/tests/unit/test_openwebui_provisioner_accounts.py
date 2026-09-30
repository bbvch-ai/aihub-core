from collections.abc import Iterator
from contextlib import contextmanager
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
    async def test_should_create_account_when_group_member_has_no_account(
        self, provisioner: OpenWebuiProvisioner
    ) -> None:
        with patch.object(provisioner._openwebui, "create_user", return_value=_owui_user("a@x", "owui-a")) as create:
            provisioned = await provisioner._provision_missing_accounts([_keycloak_user("kc-a", "a@x")], {"kc-a"}, {})

        create.assert_awaited_once_with(email="a@x", display_name="New User", external_id="kc-a", scim=None)
        assert provisioned == {"kc-a": "owui-a"}

    @pytest.mark.asyncio
    async def test_should_not_create_account_when_user_joins_no_group(self, provisioner: OpenWebuiProvisioner) -> None:
        with patch.object(provisioner._openwebui, "create_user") as create:
            await provisioner._provision_missing_accounts([_keycloak_user("kc-a", "a@x")], set(), {})

        create.assert_not_called()

    @pytest.mark.asyncio
    async def test_should_not_create_account_when_one_exists(self, provisioner: OpenWebuiProvisioner) -> None:
        with patch.object(provisioner._openwebui, "create_user") as create:
            await provisioner._provision_missing_accounts(
                [_keycloak_user("kc-a", "a@x")], {"kc-a"}, {"kc-a": "owui-a"}
            )

        create.assert_not_called()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("user", [_keycloak_user("kc-a", ""), _keycloak_user("kc-a", "a@x", enabled=False)])
    async def test_should_not_create_account_when_user_has_no_email_or_is_disabled(
        self, provisioner: OpenWebuiProvisioner, user: KeycloakUser
    ) -> None:
        with patch.object(provisioner._openwebui, "create_user") as create:
            await provisioner._provision_missing_accounts([user], {"kc-a"}, {})

        create.assert_not_called()


class TestProvisioningDuringGroupSync:
    """The user's first role triggers a sync before their first chat login created an account."""

    @contextmanager
    def _group_sync(
        self, provisioner: OpenWebuiProvisioner, *, active_user_ids: set[str], role_holders: list[str]
    ) -> Iterator[tuple[MagicMock, MagicMock]]:
        with (
            patch(f"{_MODULE}.TenantMetadataEntity") as mock_tenant,
            patch(f"{_MODULE}.RoleEntity") as mock_role,
            patch(f"{_MODULE}.UserTenantRoleEntity") as mock_utr,
            patch(f"{_MODULE}.KeycloakAdminService") as mock_keycloak,
            patch.object(provisioner._openwebui, "list_groups", return_value=[_group("aihub:T1:R1", "grp-1")]),
            patch.object(provisioner._openwebui, "list_users", return_value=[]),
            patch.object(provisioner._openwebui, "create_user", return_value=_owui_user("a@x", "owui-a")) as create,
            patch.object(provisioner._openwebui, "update_group_members") as update_members,
        ):
            tenant = MagicMock()
            tenant.name, tenant.id, tenant.access_rules = "T1", "tid-1", []
            mock_tenant.objects.return_value = [tenant]
            role = MagicMock()
            role.name, role.access_rules = "R1", []
            mock_role.get_roles_for_tenant.return_value = [role]
            mock_keycloak.get_all_users = AsyncMock(return_value=[_keycloak_user("kc-a", "a@x")])
            mock_keycloak.get_user_ids_with_active_tenant = AsyncMock(return_value=active_user_ids)
            mock_utr.objects.return_value = [MagicMock(user_id=uid) for uid in role_holders]
            yield create, update_members

    @pytest.mark.asyncio
    async def test_should_add_provisioned_account_to_role_group(self, provisioner: OpenWebuiProvisioner) -> None:
        with self._group_sync(provisioner, active_user_ids={"kc-a"}, role_holders=["kc-a"]) as (_, update_members):
            await provisioner._sync_groups()

        update_members.assert_awaited_once_with("grp-1", ["owui-a"], scim=ANY)

    @pytest.mark.asyncio
    async def test_should_not_create_account_before_user_has_an_active_tenant(
        self, provisioner: OpenWebuiProvisioner
    ) -> None:
        """A role assigned before the user's first login: the account follows once their active tenant is set."""
        with self._group_sync(provisioner, active_user_ids=set(), role_holders=["kc-a"]) as (create, _):
            await provisioner._sync_groups()

        create.assert_not_called()

    @pytest.mark.asyncio
    async def test_should_not_create_account_when_user_holds_no_role(self, provisioner: OpenWebuiProvisioner) -> None:
        """Revoking a user's last role leaves their association with ``roles=[]``, which joins no group."""
        with self._group_sync(provisioner, active_user_ids={"kc-a"}, role_holders=[]) as (create, _):
            await provisioner._sync_groups()

        create.assert_not_called()
