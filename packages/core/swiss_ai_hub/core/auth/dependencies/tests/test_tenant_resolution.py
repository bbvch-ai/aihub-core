from collections.abc import Generator
from typing import Any

import pytest
from fastapi import HTTPException, Request
from mongoengine import connect, disconnect
from pytest_bdd import given, parsers, scenarios, then, when

from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.access.entities.role_entity import RoleEntity
from swiss_ai_hub.core.persistence.access.entities.tenant_entity import TenantEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.persistence.user.user_entity import UserEntity

scenarios("features/tenant_resolution.feature")


class ConcreteAuthHandler(AuthHandler):
    """Concrete implementation of AuthHandler for testing tenant resolution methods."""

    async def __call__(self, request: Request) -> UserIdentity:
        raise NotImplementedError("Not used in tenant resolution tests")

    async def authenticate_token(self, token: str) -> UserIdentity:
        raise NotImplementedError("Not used in tenant resolution tests")


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


@pytest.fixture
def auth_handler() -> ConcreteAuthHandler:
    """Create an auth handler instance for testing."""
    return ConcreteAuthHandler()


def create_mock_request(
    path_params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> Request:
    """Create a mock FastAPI Request with the given path params and headers."""
    headers = headers or {}
    headers_list = [(k.lower().encode("utf8"), v.encode("utf8")) for k, v in headers.items()]
    scope: dict[str, Any] = {
        "type": "http",
        "headers": headers_list,
        "method": "GET",
        "path": "/",
        "path_params": path_params or {},
    }
    return Request(scope)


# --- Background Steps ---


@given(parsers.parse('the default tenant exists with name "{name}" and access rules "{access_rules}"'))
def ensure_default_tenant(cleanup_documents: list[Any], context: dict[str, Any], name: str, access_rules: str) -> None:
    """Ensure the default tenant exists with the exact name specified."""
    rules_list = [r.strip() for r in access_rules.split(",")]
    # Remove all existing default tenants to guarantee clean test state
    TenantEntity.objects(is_default=True).delete()
    tenant = TenantEntity.create_tenant(
        name=name,
        description="Default tenant for testing",
        access_rules=rules_list,
        is_default=True,
    )
    context["default_tenant"] = tenant
    cleanup_documents.append(tenant)


@given(parsers.parse('a second tenant exists with name "{name}" and access rules "{access_rules}"'))
def create_second_tenant(cleanup_documents: list[Any], context: dict[str, Any], name: str, access_rules: str) -> None:
    """Create a second tenant."""
    rules_list = [r.strip() for r in access_rules.split(",")]
    tenant = TenantEntity.create_tenant(
        name=name,
        description="Second tenant for testing",
        access_rules=rules_list,
    )
    context["second_tenant"] = tenant
    cleanup_documents.append(tenant)


@given(parsers.parse('the system role "{role_name}" exists'))
def ensure_system_role(cleanup_documents: list[Any], role_name: str) -> None:
    """Ensure a system role exists."""
    existing = RoleEntity.get_system_role_by_name(role_name)
    if existing:
        return

    role = RoleEntity.create_system_role(
        name=role_name,
        description=f"System role {role_name} for testing",
        access_rules=["aihub.user.>"],
    )
    cleanup_documents.append(role)


@given(parsers.parse('user "{user_id}" is a member of the default tenant with roles "{roles}"'))
def add_user_to_default_tenant(cleanup_documents: list[Any], context: dict[str, Any], user_id: str, roles: str) -> None:
    """Add a user to the default tenant with the given roles."""
    tenant = context["default_tenant"]
    roles_list = [r.strip() for r in roles.split(",")]
    association = UserTenantRoleEntity.create_or_update(
        user_id=user_id,
        tenant_id=str(tenant.id),
        roles=roles_list,
    )
    cleanup_documents.append(association)


@given(parsers.parse('user "{user_id}" is a member of the second tenant with roles "{roles}"'))
def add_user_to_second_tenant(cleanup_documents: list[Any], context: dict[str, Any], user_id: str, roles: str) -> None:
    """Add a user to the second tenant with the given roles."""
    tenant = context["second_tenant"]
    roles_list = [r.strip() for r in roles.split(",")]
    association = UserTenantRoleEntity.create_or_update(
        user_id=user_id,
        tenant_id=str(tenant.id),
        roles=roles_list,
    )
    cleanup_documents.append(association)


@given(parsers.parse('user "{user_id}" is a member of the default tenant only with roles "{roles}"'))
def add_user_to_default_only(cleanup_documents: list[Any], context: dict[str, Any], user_id: str, roles: str) -> None:
    """Add a user to the default tenant only."""
    add_user_to_default_tenant(cleanup_documents, context, user_id, roles)


@given(parsers.parse('user "{user_id}" is a member of the second tenant only with roles "{roles}"'))
def add_user_to_second_only(cleanup_documents: list[Any], context: dict[str, Any], user_id: str, roles: str) -> None:
    """Add a user to the second tenant only."""
    add_user_to_second_tenant(cleanup_documents, context, user_id, roles)


# --- Active Tenant Steps ---


def ensure_user_entity(cleanup_documents: list[Any], user_id: str) -> UserEntity:
    """Ensure a UserEntity exists for the given user_id."""
    user = UserEntity.objects(id=user_id).first()
    if not user:
        user = UserEntity.create_user(oid=user_id, name=f"Test User {user_id}", email=f"{user_id}@test.local")
        cleanup_documents.append(user)
    return user


@given(parsers.parse('user "{user_id}" has active tenant set to the second tenant'))
def set_active_tenant_to_second(cleanup_documents: list[Any], context: dict[str, Any], user_id: str) -> None:
    """Set a user's active tenant to the second tenant."""
    user = ensure_user_entity(cleanup_documents, user_id)
    user.set_active_tenant(str(context["second_tenant"].id))


@given(parsers.parse('user "{user_id}" has active tenant set to the default tenant'))
def set_active_tenant_to_default(cleanup_documents: list[Any], context: dict[str, Any], user_id: str) -> None:
    """Set a user's active tenant to the default tenant."""
    user = ensure_user_entity(cleanup_documents, user_id)
    user.set_active_tenant(str(context["default_tenant"].id))


@given(parsers.parse('user "{user_id}" has active tenant set to "{tenant_id}"'))
def set_active_tenant_to_id(cleanup_documents: list[Any], user_id: str, tenant_id: str) -> None:
    """Set a user's active tenant to a specific ID (possibly non-existent)."""
    user = ensure_user_entity(cleanup_documents, user_id)
    user.active_tenant_id = tenant_id
    user.save()


# --- Given Steps for Request Context ---


@given("a request with tenant path parameter set to the second tenant")
def request_with_second_tenant_path_param(context: dict[str, Any]) -> None:
    """Create a request with tenant_id path parameter pointing to the second tenant."""
    tenant = context["second_tenant"]
    context["request"] = create_mock_request(path_params={"tenant_id": str(tenant.id)})


@given(parsers.parse('a request with tenant path parameter set to "{tenant_id}"'))
def request_with_specific_tenant_path_param(context: dict[str, Any], tenant_id: str) -> None:
    """Create a request with tenant_id path parameter set to a specific value."""
    context["request"] = create_mock_request(path_params={"tenant_id": tenant_id})


@given("no default tenant exists")
def remove_default_tenant(context: dict[str, Any]) -> None:
    """Remove the default tenant to simulate no default tenant scenario."""
    tenant = context.get("default_tenant")
    if tenant:
        # Temporarily mark it as not default for this test
        tenant.is_default = False
        tenant.save()
        context["_original_default_state"] = True


# --- When Steps ---


@when(parsers.parse('the auth handler resolves tenant for user "{user_id}"'))
def resolve_tenant(context: dict[str, Any], auth_handler: ConcreteAuthHandler, user_id: str) -> None:
    """Resolve tenant for the given user."""
    request = context["request"]
    tenant_identity = auth_handler.resolve_tenant_for_user(request, user_id)
    context["resolved_tenant"] = tenant_identity


@when(parsers.parse('the auth handler resolves tenant for user "{user_id}" expecting error'))
def resolve_tenant_expect_error(context: dict[str, Any], auth_handler: ConcreteAuthHandler, user_id: str) -> None:
    """Resolve tenant for the given user, expecting an error."""
    request = context["request"]
    try:
        auth_handler.resolve_tenant_for_user(request, user_id)
        pytest.fail("Expected an HTTPException but none was raised")
    except HTTPException as e:
        context["error"] = e
    finally:
        # Restore default tenant state if it was modified
        if context.get("_original_default_state"):
            tenant = context.get("default_tenant")
            if tenant:
                tenant.is_default = True
                tenant.save()


@when(parsers.parse('the auth handler gets active tenant for user "{user_id}"'))
def get_active_tenant(context: dict[str, Any], auth_handler: ConcreteAuthHandler, user_id: str) -> None:
    """Get the active tenant for the given user."""
    tenant_identity = auth_handler.get_active_tenant_for_user(user_id)
    context["resolved_tenant"] = tenant_identity


@when(parsers.parse('the auth handler gets active tenant for user "{user_id}" expecting error'))
def get_active_tenant_expect_error(context: dict[str, Any], auth_handler: ConcreteAuthHandler, user_id: str) -> None:
    """Get the active tenant for the given user, expecting an error."""
    try:
        auth_handler.get_active_tenant_for_user(user_id)
        pytest.fail("Expected an HTTPException but none was raised")
    except HTTPException as e:
        context["error"] = e


# --- Then Steps ---


@then(parsers.parse('the resolved tenant should be "{expected_name}"'))
def check_resolved_tenant(context: dict[str, Any], expected_name: str) -> None:
    """Check that the resolved tenant has the expected name."""
    tenant = context.get("resolved_tenant")
    assert tenant is not None, "No tenant was resolved"
    assert tenant.name == expected_name, f"Expected tenant name '{expected_name}', got '{tenant.name}'"


@then(parsers.parse('a {status_code:d} error should be raised with message "{expected_message}"'))
def check_error_status_and_message(context: dict[str, Any], status_code: int, expected_message: str) -> None:
    """Check that an HTTP error was raised with the expected status code and message."""
    error = context.get("error")
    assert error is not None, "No error was captured"
    assert error.status_code == status_code, f"Expected status {status_code}, got {error.status_code}"
    assert expected_message in error.detail, f"Expected message '{expected_message}' in '{error.detail}'"


@then(parsers.parse('user "{user_id}" should have active tenant set to the second tenant'))
def check_active_tenant_is_second(context: dict[str, Any], user_id: str) -> None:
    """Verify the user's active tenant was updated to the second tenant."""
    user = UserEntity.objects(id=user_id).only("active_tenant_id").first()
    expected = str(context["second_tenant"].id)
    assert user is not None, f"User {user_id} not found"
    assert user.active_tenant_id == expected, f"Expected active_tenant_id '{expected}', got '{user.active_tenant_id}'"


@then(parsers.parse('user "{user_id}" should have active tenant set to the default tenant'))
def check_active_tenant_is_default(context: dict[str, Any], user_id: str) -> None:
    """Verify the user's active tenant was updated to the default tenant."""
    user = UserEntity.objects(id=user_id).only("active_tenant_id").first()
    expected = str(context["default_tenant"].id)
    assert user is not None, f"User {user_id} not found"
    assert user.active_tenant_id == expected, f"Expected active_tenant_id '{expected}', got '{user.active_tenant_id}'"
