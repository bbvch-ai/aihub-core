from collections.abc import Generator
from typing import Any

import pytest
from mongoengine import connect, disconnect
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_lib.auth.access.AccessChecker import AccessChecker, AccessLevel
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity
from aihub_lib.persistence.access.entities.TenantEntity import TenantEntity
from aihub_lib.persistence.access.entities.UserTenantRoleEntity import UserTenantRoleEntity

scenarios("features/multi_tenant_access.feature")


@pytest.fixture(autouse=True)
def mongo_connection() -> Generator[None]:
    """Set up a MongoDB connection for testing and disconnect after."""
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
    )
    yield
    disconnect()


@pytest.fixture
def context() -> dict[str, Any]:
    """A dictionary to hold state between BDD steps."""
    return {"tenants": {}, "users": {}}


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


@given(parsers.parse('tenant "{name}" exists with access rules "{access_rules}"'))
def create_tenant(cleanup_documents: list[Any], context: dict[str, Any], name: str, access_rules: str) -> None:
    """Create a tenant with the given access rules."""
    rules_list = [r.strip() for r in access_rules.split(",")]
    tenant = TenantEntity.create_tenant(
        name=name,
        description=f"Tenant {name} for testing",
        access_rules=rules_list,
    )
    context["tenants"][name] = tenant
    cleanup_documents.append(tenant)


@given(parsers.parse('the system role "{role_name}" exists with access rules "{access_rules}"'))
def ensure_system_role(cleanup_documents: list[Any], role_name: str, access_rules: str) -> None:
    """Ensure a system role exists with the given access rules."""
    existing = RoleEntity.get_system_role_by_name(role_name)
    if existing:
        return

    rules_list = [r.strip() for r in access_rules.split(",")]
    role = RoleEntity.create_system_role(
        name=role_name,
        description=f"System role {role_name} for testing",
        access_rules=rules_list,
    )
    cleanup_documents.append(role)


# --- Given Steps ---


@given(parsers.parse('user "{user_id}" has role "{role_name}" in tenant "{tenant_name}"'))
def assign_role_to_user(
    cleanup_documents: list[Any], context: dict[str, Any], user_id: str, role_name: str, tenant_name: str
) -> None:
    """Assign a role to a user in a specific tenant."""
    tenant = context["tenants"][tenant_name]
    association = UserTenantRoleEntity.create_or_update(
        user_id=user_id,
        tenant_id=tenant.id,
        roles=[role_name],
    )
    cleanup_documents.append(association)

    # Store user info in context for later use
    if user_id not in context["users"]:
        context["users"][user_id] = {}
    context["users"][user_id][tenant_name] = {
        "tenant_id": tenant.id,
        "roles": [role_name],
    }


# --- When Steps ---


@when(parsers.parse('checking access for user "{user_id}" in tenant "{tenant_name}" to "{permission_template}"'))
def check_access(context: dict[str, Any], user_id: str, tenant_name: str, permission_template: str) -> None:
    """Check access for a user in a specific tenant."""
    tenant = context["tenants"][tenant_name]

    # Get user's roles in this tenant
    user_roles = UserTenantRoleEntity.get_roles_for_user_in_tenant(user_id, tenant.id)

    # Get access rules from the user's roles
    user_access_rules = RoleEntity.get_access_rules_for_roles(user_roles, tenant.id)

    # Create access checker with both user and tenant access rules
    checker = AccessChecker(list(user_access_rules), tenant_access_rules=tenant.access_rules)
    access_level = checker.access_level(permission_template)

    context["last_access_level"] = access_level


# --- Then Steps ---


@then(parsers.parse("the access level should be {expected_level}"))
def verify_access_level(context: dict[str, Any], expected_level: str) -> None:
    """Verify the access level matches the expected value."""
    try:
        expected = AccessLevel[expected_level]
    except KeyError:
        pytest.fail(f"Invalid expected level '{expected_level}' in feature file.")

    actual = context.get("last_access_level")
    assert actual is expected, f"Expected {expected}, but got {actual}"
