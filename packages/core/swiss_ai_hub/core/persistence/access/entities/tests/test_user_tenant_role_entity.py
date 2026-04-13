import asyncio
from collections.abc import Generator
from typing import Any
from unittest.mock import patch

import pytest
from mongoengine import connect, disconnect
from pytest_bdd import given, parsers, scenarios, then, when

from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.tenant_entity import TenantEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

scenarios("features/user_tenant_role_entity.feature")


@pytest.fixture(autouse=True)
def mongo_connection() -> Generator[None]:
    """Set up a MongoDB connection for testing and disconnect after."""
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
    )
    yield
    disconnect()


@pytest.fixture(autouse=True)
def mock_keycloak_active_tenant():
    """Mock KeycloakAdminService active tenant methods for tests."""

    async def mock_get_active_tenant_id(user_id: str) -> str | None:
        return None

    async def mock_set_active_tenant(user_id: str, tenant_id: str) -> None:
        pass

    async def mock_clear_active_tenant(user_id: str) -> None:
        pass

    with (
        patch.object(KeycloakAdminService, "get_active_tenant_id", side_effect=mock_get_active_tenant_id),
        patch.object(KeycloakAdminService, "set_active_tenant", side_effect=mock_set_active_tenant),
        patch.object(KeycloakAdminService, "clear_active_tenant", side_effect=mock_clear_active_tenant),
    ):
        yield


@pytest.fixture
def context() -> dict[str, Any]:
    """A dictionary to hold state between BDD steps."""
    return {}


@pytest.fixture
def cleanup_documents() -> Generator[list[Any]]:
    """Collect inserted documents for cleanup after the test."""
    inserted_documents: list[Any] = []
    yield inserted_documents
    for doc in inserted_documents:
        try:
            doc.delete()
        except Exception:
            pass


# --- Background Steps ---


@given(parsers.parse('the default tenant exists with access rules "{access_rules}"'))
def ensure_default_tenant(cleanup_documents: list[Any], context: dict[str, Any], access_rules: str) -> None:
    """Ensure the default tenant exists."""
    rules_list = [r.strip() for r in access_rules.split(",")]
    tenant = TenantEntity.ensure_default_tenant_exists(
        name="Test Default Tenant",
        description="Default tenant for testing",
        access_rules=rules_list,
    )
    context["default_tenant"] = tenant
    cleanup_documents.append(tenant)


@given(parsers.parse('the system role "{role_name}" exists with access rules "{access_rules}"'))
def ensure_system_role(cleanup_documents: list[Any], role_name: str, access_rules: str) -> None:
    """Ensure a system role exists."""
    rules_list = [r.strip() for r in access_rules.split(",")]
    existing = RoleEntity.get_system_role_by_name(role_name)
    if existing:
        return

    role = RoleEntity.create_system_role(
        name=role_name,
        description=f"System role {role_name} for testing",
        access_rules=rules_list,
    )
    cleanup_documents.append(role)


# --- Given Steps ---


@given(parsers.parse('a user "{user_id}" does not have an association with the default tenant'))
def ensure_no_association(context: dict[str, Any], user_id: str) -> None:
    """Ensure the user does not have an association with the default tenant."""
    tenant = context["default_tenant"]
    asyncio.run(UserTenantRoleEntity.remove_user_from_tenant(user_id, str(tenant.id)))


@given(parsers.parse('a user "{user_id}" has roles "{roles}" in the default tenant'))
def create_user_with_roles(context: dict[str, Any], cleanup_documents: list[Any], user_id: str, roles: str) -> None:
    """Create an association for the user with the given roles."""
    tenant = context["default_tenant"]
    roles_list = [r.strip() for r in roles.split(",")]
    association = UserTenantRoleEntity.create_or_update(
        user_id=user_id,
        tenant_id=str(tenant.id),
        roles=roles_list,
    )
    cleanup_documents.append(association)


# --- When Steps ---


@when(parsers.parse('I create an association for user "{user_id}" with roles "{roles}"'))
def create_association(context: dict[str, Any], cleanup_documents: list[Any], user_id: str, roles: str) -> None:
    """Create a new user-tenant-role association."""
    tenant = context["default_tenant"]
    roles_list = [r.strip() for r in roles.split(",")]
    association = UserTenantRoleEntity.create_or_update(
        user_id=user_id,
        tenant_id=str(tenant.id),
        roles=roles_list,
    )
    context["created_association"] = association
    cleanup_documents.append(association)


@when(parsers.parse('I update the association for user "{user_id}" with roles "{roles}"'))
def update_association(context: dict[str, Any], user_id: str, roles: str) -> None:
    """Update an existing user-tenant-role association."""
    tenant = context["default_tenant"]
    roles_list = [r.strip() for r in roles.split(",")]
    UserTenantRoleEntity.create_or_update(
        user_id=user_id,
        tenant_id=str(tenant.id),
        roles=roles_list,
    )


@when(parsers.parse('I add roles "{roles}" to user "{user_id}" in the default tenant'))
def add_roles(context: dict[str, Any], user_id: str, roles: str) -> None:
    """Add roles to an existing association."""
    tenant = context["default_tenant"]
    roles_list = [r.strip() for r in roles.split(",")]
    UserTenantRoleEntity.add_roles(user_id, str(tenant.id), roles_list)


@when(parsers.parse('I remove roles "{roles}" from user "{user_id}" in the default tenant'))
def remove_roles(context: dict[str, Any], user_id: str, roles: str) -> None:
    """Remove roles from an existing association."""
    tenant = context["default_tenant"]
    roles_list = [r.strip() for r in roles.split(",")]
    UserTenantRoleEntity.remove_roles(user_id, str(tenant.id), roles_list)


@when(parsers.parse('I remove user "{user_id}" from the default tenant'))
def remove_user(context: dict[str, Any], user_id: str) -> None:
    """Remove a user from the default tenant."""
    tenant = context["default_tenant"]
    asyncio.run(UserTenantRoleEntity.remove_user_from_tenant(user_id, str(tenant.id)))


@when(parsers.parse('I create an association for user "{user_id}" with roles "{roles}" without validation'))
def create_association_no_validation(
    context: dict[str, Any], cleanup_documents: list[Any], user_id: str, roles: str
) -> None:
    """Create a new user-tenant-role association without role validation."""
    tenant = context["default_tenant"]
    roles_list = [r.strip() for r in roles.split(",")]
    association = UserTenantRoleEntity.create_or_update(
        user_id=user_id,
        tenant_id=str(tenant.id),
        roles=roles_list,
        validate_roles=False,
    )
    context["created_association"] = association
    cleanup_documents.append(association)


# --- Then Steps ---


@then(parsers.parse('user "{user_id}" should have roles "{expected_roles}" in the default tenant'))
def check_user_roles(context: dict[str, Any], user_id: str, expected_roles: str) -> None:
    """Check that the user has the expected roles."""
    tenant = context["default_tenant"]
    expected_set = {r.strip() for r in expected_roles.split(",")}
    actual_roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, str(tenant.id))
    assert set(actual_roles) == expected_set, f"Expected roles {expected_set}, got {set(actual_roles)}"


@then(parsers.parse('user "{user_id}" should have no association with the default tenant'))
def check_no_association(context: dict[str, Any], user_id: str) -> None:
    """Check that the user has no association with the default tenant."""
    tenant = context["default_tenant"]
    association = UserTenantRoleEntity.get_by_user_and_tenant(user_id, str(tenant.id))
    assert association is None, f"Expected no association, but found one with roles {association.roles}"


@then(parsers.parse('user "{user_id}" should have no roles in the default tenant'))
def check_no_roles(context: dict[str, Any], user_id: str) -> None:
    """Check that the user has no roles in the default tenant."""
    tenant = context["default_tenant"]
    roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, str(tenant.id))
    assert roles == [], f"Expected no roles, but got {roles}"
