from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import Request
from pytest_bdd import given, parsers, scenarios, then, when

from swiss_ai_hub.core.auth.dependencies.dangerous_development_only_auth_handler.dangerous_development_only_auth_handler import (  # noqa: E501
    DangerousDevelopmentOnlyAuthHandler,
)
from swiss_ai_hub.core.testing.asyncio_utils.bdd import async_test

# --- Scenario Declaration ---


scenarios("features/dangerous_development_only_auth_handler.feature")


# --- Fixtures ---


@pytest.fixture(autouse=True)
def mock_database_operations(monkeypatch: pytest.MonkeyPatch):
    """Mock all database operations required by the auth handler."""
    from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity

    def mock_get_default_tenant() -> MagicMock:
        tenant = MagicMock()
        tenant.id = "default-tenant-id"
        tenant.name = "Default Tenant"
        return tenant

    def mock_create_or_update(**kwargs) -> MagicMock:
        return MagicMock()

    async def mock_get_active_tenant_id(user_id: str) -> str | None:
        return "default-tenant-id"

    async def mock_set_active_tenant(user_id: str, tenant_id: str | None) -> None:
        pass

    async def mock_resolve_tenant(_self, _request, _user_id: str) -> TenantIdentity:
        return TenantIdentity(id="default-tenant-id", name="Default Tenant", access_rules=[])

    monkeypatch.setattr(
        "swiss_ai_hub.core.persistence.access.entities.tenant_entity.TenantEntity.get_default_tenant",
        mock_get_default_tenant,
    )
    monkeypatch.setattr(
        "swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity.UserTenantRoleEntity.create_or_update",
        mock_create_or_update,
    )
    monkeypatch.setattr(
        "swiss_ai_hub.core.auth.keycloak.keycloak_admin_service.KeycloakAdminService.get_active_tenant_id",
        mock_get_active_tenant_id,
    )
    monkeypatch.setattr(
        "swiss_ai_hub.core.auth.keycloak.keycloak_admin_service.KeycloakAdminService.set_active_tenant",
        mock_set_active_tenant,
    )
    monkeypatch.setattr(
        "swiss_ai_hub.core.auth.dependencies.auth_handler.AuthHandler.resolve_tenant_for_user", mock_resolve_tenant
    )
    monkeypatch.setattr(
        "swiss_ai_hub.core.auth.dependencies.auth_handler.AuthHandler.get_active_tenant_for_user", mock_resolve_tenant
    )


@pytest.fixture
def dummy_request() -> Request:
    """Create and return a dummy Request object."""
    scope: dict[str, Any] = {
        "type": "http",
        "headers": [(b"host", b"testserver")],
        "method": "GET",
        "path": "/",
        "path_params": {"tenant_id": "active"},
    }
    return Request(scope)


@pytest.fixture
def result_user() -> dict[str, Any]:
    """Container for storing the resulting user."""
    return {}


# --- Given Steps ---


@given(parsers.parse('a NoAuth configuration with name "{name}", email "{email}", oid "{oid}", and roles "{roles}"'))
def setup_no_auth_config(monkeypatch: pytest.MonkeyPatch, name: str, email: str, oid: str, roles: str) -> None:
    """Set up the NoAuth configuration using environment variables."""
    monkeypatch.setenv("DANGEROUS_DEV_ONLY_AUTH_FAKE_NAME", name)
    monkeypatch.setenv("DANGEROUS_DEV_ONLY_AUTH_FAKE_EMAIL", email)
    monkeypatch.setenv("DANGEROUS_DEV_ONLY_AUTH_FAKE_OID", oid)
    monkeypatch.setenv("DANGEROUS_DEV_ONLY_AUTH_FAKE_ROLES", roles)


# --- When Steps ---


@when("I invoke the DangerousDevelopmentOnlyAuthHandler with a dummy request")
@async_test
async def invoke_no_auth_handler(dummy_request: Request, result_user: dict[str, Any]) -> None:
    """Invoke the DangerousDevelopmentOnlyAuthHandler and store the returned user."""
    handler = DangerousDevelopmentOnlyAuthHandler()
    user = await handler(dummy_request)
    result_user["user"] = user


# --- Then Steps ---


@then(parsers.parse('the returned user should have name "{expected_name}"'))
def check_name(result_user: dict[str, Any], expected_name: str) -> None:
    """Check that the returned user has the expected name."""
    user = result_user.get("user")
    assert user is not None, "No user returned by DangerousDevelopmentOnlyAuthHandler"
    assert user.name == expected_name, f'Expected user name "{expected_name}", got "{user.name}"'


@then(parsers.parse('the returned user should have preferred_username "{expected_email}"'))
def check_preferred_username(result_user: dict[str, Any], expected_email: str) -> None:
    """Check that the returned user has the expected preferred username."""
    user = result_user.get("user")
    assert user is not None, "No user returned by DangerousDevelopmentOnlyAuthHandler"
    assert user.email == expected_email, f'Expected preferred username "{expected_email}", got "{user.email}"'


@then(parsers.parse('the returned user should have oid "{expected_oid}"'))
def check_oid(result_user: dict[str, Any], expected_oid: str) -> None:
    """Check that the returned user has the expected oid."""
    user = result_user.get("user")
    assert user is not None, "No user returned by DangerousDevelopmentOnlyAuthHandler"
    assert user.id == expected_oid, f'Expected oid "{expected_oid}", got "{user.id}"'


@then(parsers.parse('the returned user should have roles "{role1}" and "{role2}"'))
def check_roles(result_user: dict[str, Any], role1: str, role2: str) -> None:
    """Check that the returned user has the expected roles."""
    user = result_user.get("user")
    assert user is not None, "No user returned by DangerousDevelopmentOnlyAuthHandler"
    assert set(user.roles) == {role1, role2}, f"Expected roles {role1}, {role2}, got {user.roles}"
