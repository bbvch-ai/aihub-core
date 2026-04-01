import secrets
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from bson import ObjectId
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer
from mongoengine import connect, disconnect
from pytest_bdd import given, parsers, scenarios, then, when

from swiss_ai_hub.core.auth.dependencies.token_auth_handler.token_auth_handler import TokenAuthHandler
from swiss_ai_hub.core.infrastructure.api.ai_hub_settings import AIHubSettings
from swiss_ai_hub.core.infrastructure.mongo.mongo_settings import MongoSettings
from swiss_ai_hub.core.persistence.access.entities.bearer_token import BearerToken
from swiss_ai_hub.core.persistence.access.entities.tenant_entity import TenantEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.persistence.user.user_entity import UserEntity
from swiss_ai_hub.core.testing.asyncio_utils.bdd import async_test

# --- MongoDB Connection Fixture ---


@pytest.fixture(autouse=True)
def mongo_connection(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    """Set up a MongoDB connection for testing and disconnect after."""
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
    )

    # Ensure default tenant exists for multi-tenant auth tests
    TenantEntity.ensure_default_tenant_exists(
        name="Default Tenant",
        description="Default tenant for testing",
        access_rules=["aihub.admin.>"],
    )

    yield
    disconnect()


# --- Scenario Declarations ---


scenarios("features/token_auth_handler.feature")


# --- Common Fixtures and Helpers ---


@pytest.fixture
def token_context() -> dict[str, Any]:
    """Store token values (e.g. token string and expected user id) across steps."""
    return {}


@pytest.fixture
def token_context_result() -> dict[str, Any]:
    """Store the authenticated user returned by TokenAuthHandler."""
    return {}


@pytest.fixture
def error_context() -> dict[str, Any]:
    """Store error information when TokenAuthHandler rejects a token."""
    return {}


@pytest.fixture
def cleanup_document() -> Generator[list[Any]]:
    """Collect inserted token documents for cleanup after the test."""
    inserted_documents: list[Any] = []
    yield inserted_documents
    for doc in inserted_documents:
        doc.delete()


def create_dummy_request(headers: dict[str, str], path_params: dict[str, str] | None = None) -> Request:
    """Create and return a dummy FastAPI Request with the given headers."""
    headers_list = [(k.lower().encode("utf8"), v.encode("utf8")) for k, v in headers.items()]
    scope: dict[str, Any] = {
        "type": "http",
        "headers": headers_list,
        "method": "GET",
        "path": "/",
        "path_params": path_params or {},
    }
    return Request(scope)


def generate_dummy_valid_token(oid: str) -> str:
    """Generate a dummy token string using the given OID (24 hex characters)."""
    random_part = secrets.token_urlsafe(128)[:128]
    return f"{oid}.{random_part}"


# --- Given Steps ---


@given(
    parsers.parse(
        'a token exists in the database with user details: name "{name}", email "{email}", and roles "{roles}"'
    )
)
def insert_token_document(
    token_context: dict[str, Any], cleanup_document: list[Any], name: str, email: str, roles: str
) -> None:
    """Insert a token document in the database with the given user details."""
    roles_list = [r.strip() for r in roles.split(",")]
    user_oid = str(ObjectId())
    user = UserEntity.create_user(
        oid=user_oid,
        name=name,
        email=email,
    )

    # Assign user to default tenant (skip role validation for test data)
    default_tenant = TenantEntity.get_default_tenant()
    if default_tenant:
        user_tenant_role = UserTenantRoleEntity.create_or_update(
            user_id=user_oid,
            tenant_id=str(default_tenant.id),
            roles=roles_list,
            validate_roles=False,
        )
        cleanup_document.append(user_tenant_role)
        token_context["tenant_id"] = str(default_tenant.id)

    expiry = datetime.now(UTC) + timedelta(hours=1)
    token_doc = BearerToken.create_new_token(
        name="token-name",
        expiry_date=expiry,
        user_oid=user_oid,
    )
    token_context["token_str"] = token_doc.token
    token_context["expected_user_oid"] = user_oid
    token_context["token_doc"] = token_doc
    token_context["user_roles"] = roles_list
    cleanup_document.append(user)
    cleanup_document.append(token_doc)


@given(parsers.parse('an invalid token format "{token}"'))
def invalid_token_format(token_context: dict[str, Any], token: str) -> None:
    """Store an invalid token format in the context."""
    token_context["token_str"] = token


@given(parsers.parse('a token does not exist in the database with token "{token}"'))
def token_not_found(token_context: dict[str, Any], token: str) -> None:
    """Store a token (formatted as <oid>.<random>) that is not found in the database."""
    parts = token.split(".")
    if len(parts) != 2 or len(parts[0]) != 24 or len(parts[1]) != 128:
        oid = parts[0] if len(parts[0]) == 24 else "123456789012345678901234"
        token = generate_dummy_valid_token(oid)
    token_context["token_str"] = token


@given("I modify the token to cause a mismatch")
def modify_token_for_mismatch(token_context: dict[str, Any]) -> None:
    """Modify the token's random part to cause a mismatch."""
    token_str = token_context["token_str"]
    parts = token_str.split(".")
    if len(parts) == 2:
        oid, random_part = parts
        new_char = "A" if random_part[0] != "A" else "B"
        new_random = new_char + random_part[1:]
        token_context["token_str"] = f"{oid}.{new_random}"
    else:
        token_context["token_str"] = token_str + "x"


@given("I set the token expiry to a past time")
def set_token_expired(token_context: dict[str, Any]) -> None:
    """Set the token's expiry date to a past time."""
    token_doc = token_context.get("token_doc")
    if token_doc:
        token_doc.expiry_date = datetime.now(UTC) - timedelta(hours=1)
        token_doc.save()


# --- When Steps ---


@when("I invoke the TokenAuthHandler with an Authorization header using the token")
@async_test
async def invoke_token_auth_handler(token_context: dict[str, Any], token_context_result: dict[str, Any]) -> None:
    """Invoke the TokenAuthHandler with the token and store the authenticated user."""
    token_str = token_context["token_str"]
    headers = {"Authorization": f"Bearer {token_str}"}
    path_params = {"tenant_id": token_context["tenant_id"]} if "tenant_id" in token_context else None
    request = create_dummy_request(headers, path_params=path_params)
    handler = TokenAuthHandler()
    try:
        security = await HTTPBearer()(request)
        user = await handler(request, security)
    except HTTPException as e:
        pytest.fail(f"TokenAuthHandler raised an unexpected exception: {e.detail}")
    token_context_result["user"] = user


@when("I invoke the TokenAuthHandler with an Authorization header using the token expecting error")
@async_test
async def invoke_token_auth_handler_expect_error(token_context: dict[str, Any], error_context: dict[str, Any]) -> None:
    """Invoke the TokenAuthHandler with the token and capture the error."""
    token_str = token_context["token_str"]
    headers = {"Authorization": f"Bearer {token_str}"}
    request = create_dummy_request(headers)
    handler = TokenAuthHandler()
    try:
        security = await HTTPBearer()(request)
        await handler(request, security)
        pytest.fail("TokenAuthHandler did not raise an exception")
    except HTTPException as e:
        error_context["error"] = e.detail


# --- Then Steps ---


@then(parsers.parse('the returned user should have name "{expected_name}"'))
def check_name(token_context_result: dict[str, Any], expected_name: str) -> None:
    """Check that the authenticated user has the expected name."""
    user = token_context_result.get("user")
    assert user is not None, "No user was returned by TokenAuthHandler"
    assert user.name == expected_name, f"Expected name '{expected_name}', got '{user.name}'"


@then(parsers.parse('the returned user should have preferred_username "{expected_email}"'))
def check_preferred_username(token_context_result: dict[str, Any], expected_email: str) -> None:
    """Check that the authenticated user has the expected preferred username."""
    user = token_context_result.get("user")
    assert user is not None, "No user was returned by TokenAuthHandler"
    assert user.email == expected_email, f"Expected email '{expected_email}', got '{user.email}'"


@then("the returned user should have oid matching the token's user id")
def check_user_oid(token_context_result: dict[str, Any], token_context: dict[str, Any]) -> None:
    """Check that the authenticated user's oid matches the expected user id."""
    user = token_context_result.get("user")
    expected_oid = token_context.get("expected_user_oid")
    assert user is not None, "No user was returned by TokenAuthHandler"
    assert user.id == expected_oid, f"Expected user oid '{expected_oid}', got '{user.id}'"


@then(parsers.parse('the returned user should have roles "{role1}" and "{role2}"'))
def check_roles(token_context_result: dict[str, Any], role1: str, role2: str) -> None:
    """Check that the authenticated user has the expected roles."""
    user = token_context_result.get("user")
    assert user is not None, "No user was returned by TokenAuthHandler"
    expected_roles = {role1, role2}
    assert set(user.roles) == expected_roles, f"Expected roles {expected_roles}, got {set(user.roles)}"


@then(parsers.parse('I should receive an HTTP error with detail "{expected_detail}"'))
def check_error_detail(error_context: dict[str, Any], expected_detail: str) -> None:
    """Check that the error detail matches the expected detail."""
    error = error_context.get("error")
    assert error == expected_detail, f"Expected error detail '{expected_detail}', got '{error}'"
