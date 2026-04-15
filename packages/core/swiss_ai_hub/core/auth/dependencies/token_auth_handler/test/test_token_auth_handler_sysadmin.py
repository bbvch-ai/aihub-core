"""Coverage for the sysadmin-via-realm-role path in ``TokenAuthHandler``.

The previous ``SuperuserAuthHandler`` had 261 lines of BDD + unit coverage that
was removed when the superuser became a real Keycloak user identified by the
``AIHubSysAdmin`` realm role (see ADR ``2026_04_14_superuser_via_keycloak_realm_role``).
The existing BDD test suite at ``test_token_auth_handler.py`` covers token
validation in general but not the ``is_sys_admin`` derivation, which is the
capability that now replaces the old handler. These tests fill that gap.
"""

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from bson import ObjectId
from mongoengine import connect, disconnect

from swiss_ai_hub.core.auth.dependencies.token_auth_handler.token_auth_handler import TokenAuthHandler
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.auth.roles import SYS_ADMIN_ROLE
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.access.entities.bearer_token import BearerToken
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.testing.auth_utils.user_mocks import register_fake_keycloak_user


@pytest.fixture(autouse=True)
def mongo_connection() -> Generator[None]:
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
    )
    TenantMetadataEntity.ensure_default_tenant_metadata_exists(
        tenant_id="default",
        name="Default Tenant",
        description="Default tenant for testing",
        access_rules=["aihub.admin.>"],
    )
    yield
    disconnect()


@pytest.fixture
def seeded_token() -> Generator[tuple[str, str]]:
    """Creates a valid bearer token backed by a fake Keycloak user that is a member
    of the default tenant.

    Yields ``(token_str, user_oid)``. The fake Keycloak admin derives group membership
    from ``UserTenantRoleEntity`` rows, so the association is what makes
    ``_resolve_active_tenant`` succeed in ``build_identity``.
    """
    user_oid = str(ObjectId())
    register_fake_keycloak_user(user_id=user_oid, name="Token Holder", email="holder@example.com")

    association = UserTenantRoleEntity.create_or_update(
        user_id=user_oid,
        tenant_id="default",
        roles=["AIHubUser"],
        validate_roles=False,
    )
    token_doc = BearerToken.create_new_token(
        name="sysadmin-test-token",
        expiry_date=datetime.now(UTC) + timedelta(hours=1),
        user_oid=user_oid,
    )
    try:
        yield token_doc.token, user_oid
    finally:
        token_doc.delete()
        association.delete()


@pytest.mark.asyncio
async def test_token_owner_with_sys_admin_realm_role_is_marked_sys_admin(
    monkeypatch: pytest.MonkeyPatch, seeded_token: tuple[str, str]
) -> None:
    """Token owner carrying the ``AIHubSysAdmin`` realm role → ``is_sys_admin=True``.

    This is the capability that replaced the deleted SuperuserAuthHandler — a bearer
    token holder must now receive sysadmin access exactly when their Keycloak user
    has the sysadmin realm role, not by virtue of the token itself.
    """
    token_str, user_oid = seeded_token
    monkeypatch.setattr(
        KeycloakAdminService,
        "get_user_realm_roles",
        AsyncMock(return_value=[SYS_ADMIN_ROLE, "AIHubUser"]),
    )

    identity = await TokenAuthHandler().authenticate_token(token_str)

    assert identity.id == user_oid
    assert identity.is_sys_admin is True


@pytest.mark.asyncio
async def test_token_owner_without_sys_admin_realm_role_is_not_sys_admin(
    monkeypatch: pytest.MonkeyPatch, seeded_token: tuple[str, str]
) -> None:
    token_str, _ = seeded_token
    monkeypatch.setattr(
        KeycloakAdminService,
        "get_user_realm_roles",
        AsyncMock(return_value=["AIHubUser", "AIHubAgentAdmin"]),
    )

    identity = await TokenAuthHandler().authenticate_token(token_str)

    assert identity.is_sys_admin is False


@pytest.mark.asyncio
async def test_token_owner_with_empty_realm_roles_is_not_sys_admin(
    monkeypatch: pytest.MonkeyPatch, seeded_token: tuple[str, str]
) -> None:
    token_str, _ = seeded_token
    monkeypatch.setattr(KeycloakAdminService, "get_user_realm_roles", AsyncMock(return_value=[]))

    identity = await TokenAuthHandler().authenticate_token(token_str)

    assert identity.is_sys_admin is False


@pytest.mark.asyncio
async def test_sys_admin_flag_reflects_only_the_specific_sys_admin_realm_role(
    monkeypatch: pytest.MonkeyPatch, seeded_token: tuple[str, str]
) -> None:
    """Guardrail: a realm role whose name merely *contains* ``AIHubSysAdmin`` must not
    be accepted as the sysadmin role. The check is strict equality against
    ``SYS_ADMIN_ROLE``, not a substring match."""
    token_str, _ = seeded_token
    monkeypatch.setattr(
        KeycloakAdminService,
        "get_user_realm_roles",
        AsyncMock(return_value=["AIHubSysAdmin-readonly", "NotAIHubSysAdmin", "aihubsysadmin"]),
    )

    identity = await TokenAuthHandler().authenticate_token(token_str)

    assert identity.is_sys_admin is False
