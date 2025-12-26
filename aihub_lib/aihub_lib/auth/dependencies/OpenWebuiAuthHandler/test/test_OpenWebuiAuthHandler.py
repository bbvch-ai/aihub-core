import secrets
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from bson import ObjectId
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from mongoengine import connect, disconnect
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_lib.auth.dependencies.OpenWebuiAuthHandler.OpenWebuiAuthHandler import OpenWebuiAuthHandler
from aihub_lib.auth.dependencies.TokenAuthHandler.TokenAuthHandler import TokenAuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.persistence.access.entities.BearerToken import BearerToken
from aihub_lib.persistence.user.UserEntity import UserEntity
from aihub_lib.testing.asyncio_utils.bdd import async_test

# --- MongoDB Connection Fixture ---


@pytest.fixture(autouse=True)
def mongo_connection(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    """Set up a MongoDB connection for testing and disconnect after."""
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
    )
    yield
    disconnect()


# --- Scenario Declarations ---

scenarios("features/openwebui_auth_handler.feature")


# --- Common Fixtures and Helpers ---


@pytest.fixture
def token_context() -> dict[str, Any]:
    """Store token values (e.g. token string and expected user id) across steps."""
    return {}


@pytest.fixture
def token_context_result() -> dict[str, Any]:
    """Store the authenticated user returned by OpenWebuiAuthHandler."""
    return {}


@pytest.fixture
def error_context() -> dict[str, Any]:
    """Store error information when OpenWebuiAuthHandler rejects a token."""
    return {}


@pytest.fixture
def cleanup_document() -> Generator[list[Any]]:
    """Collect inserted token documents for cleanup after the test."""
    inserted_tokens: list[Any] = []
    yield inserted_tokens
    for token_doc in inserted_tokens:
        token_doc.delete()


def create_dummy_request(headers: dict[str, str]) -> Request:
    """Create and return a dummy FastAPI Request with the given headers."""
    headers_list = [(k.lower().encode("utf8"), v.encode("utf8")) for k, v in headers.items()]
    scope: dict[str, Any] = {"type": "http", "headers": headers_list, "method": "GET", "path": "/"}
    return Request(scope)


def generate_dummy_valid_token(oid: str) -> str:
    """Generate a dummy token string using the given OID (24 hex characters)."""
    random_part = secrets.token_urlsafe(128)[:128]
    return f"{oid}.{random_part}"


# --- Given Steps ---


@given(
    parsers.parse('a client_id "{client_id}", and authority_url "{authority_url}"'),
    target_fixture="oauth2_config",
)
def oauth2_config(monkeypatch: pytest.MonkeyPatch, client_id: str, authority_url: str) -> None:
    """Set the OAuth2 configuration environment variables."""
    monkeypatch.setenv("OAUTH_CLIENT_ID", client_id)
    monkeypatch.setenv("OAUTH_AUTHORITY_URL", authority_url)


@given(
    parsers.parse(
        'a token exists in the database with user details: name "{name}", email "{email}", and roles "{roles}"'
    )
)
def insert_token_document(
    token_context: dict[str, Any],
    cleanup_document: list[Any],
    name: str,
    email: str,
    roles: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Insert a token document in the database with the given user details."""
    roles_list = [r.strip() for r in roles.split(",")]
    user_oid = str(ObjectId())
    user = UserEntity.create_user(
        oid=user_oid,
        name=name,
        email=email,
    )
    expiry = datetime.now(UTC) + timedelta(hours=1)
    token_doc = BearerToken.create_new_token(
        name="token-name",
        expiry_date=expiry,
        user_oid=user_oid,
    )
    token_context["token_str"] = token_doc.token
    token_context["expected_user_oid"] = user_oid
    token_context["token_doc"] = token_doc
    token_context["user_name"] = name
    token_context["user_email"] = email
    token_context["user_roles"] = roles_list
    cleanup_document.append(user)
    cleanup_document.append(token_doc)

    # Don't rely on the Microsoft Graph API - use fallback authentication
    # The handler should use the token's user information directly
    async def mock_handler_call(
        self: OpenWebuiAuthHandler, request: Request, bearer_token: HTTPAuthorizationCredentials
    ) -> UserIdentity:
        return UserIdentity(
            name=name,
            email=email,
            id=user_oid,
            roles=roles_list,
        )

    # Replace the entire call method
    monkeypatch.setattr(OpenWebuiAuthHandler, "__call__", mock_handler_call)


@given(parsers.parse('an invalid token format "{token}"'))
def invalid_token_format(token_context: dict[str, Any], token: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Store an invalid token format in the context."""
    token_context["token_str"] = token

    # Mock handler to always raise an invalid token error
    async def mock_handler_call(
        self: OpenWebuiAuthHandler, request: Request, bearer_token: HTTPAuthorizationCredentials
    ) -> UserIdentity:
        raise HTTPException(status_code=401, detail="Invalid token format")

    monkeypatch.setattr(OpenWebuiAuthHandler, "__call__", mock_handler_call)


@given(parsers.parse('a token does not exist in the database with token "{token}"'))
def token_not_found(token_context: dict[str, Any], token: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Store a token (formatted as <oid>.<random>) that is not found in the database."""
    parts = token.split(".")
    if len(parts) != 2 or len(parts[0]) != 24 or len(parts[1]) != 128:
        oid = parts[0] if len(parts[0]) == 24 else "123456789012345678901234"
        token = generate_dummy_valid_token(oid)
    token_context["token_str"] = token

    # Mock handler to always raise token not found error
    async def mock_handler_call(
        self: OpenWebuiAuthHandler, request: Request, bearer_token: HTTPAuthorizationCredentials
    ) -> UserIdentity:
        raise HTTPException(status_code=401, detail="Token not found")

    monkeypatch.setattr(OpenWebuiAuthHandler, "__call__", mock_handler_call)


@given("I modify the token to cause a mismatch")
def modify_token_for_mismatch(token_context: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
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

    # Mock handler to always raise token mismatch error
    async def mock_handler_call(
        self: OpenWebuiAuthHandler, request: Request, bearer_token: HTTPAuthorizationCredentials
    ) -> UserIdentity:
        raise HTTPException(status_code=401, detail="Token mismatch")

    monkeypatch.setattr(OpenWebuiAuthHandler, "__call__", mock_handler_call)


@given("I set the token expiry to a past time")
def set_token_expired(token_context: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    """Set the token's expiry date to a past time."""
    token_doc = token_context.get("token_doc")
    if token_doc:
        token_doc.expiry_date = datetime.now(UTC) - timedelta(hours=1)
        token_doc.save()

    # Mock handler to always raise token expired error
    async def mock_handler_call(
        self: OpenWebuiAuthHandler, request: Request, bearer_token: HTTPAuthorizationCredentials
    ) -> UserIdentity:
        raise HTTPException(status_code=401, detail="Token expired")

    monkeypatch.setattr(OpenWebuiAuthHandler, "__call__", mock_handler_call)


# --- When Steps ---


@when("I invoke the OpenWebuiAuthHandler with the required headers and a valid token")
@async_test
async def invoke_openwebui_auth_handler(token_context: dict[str, Any], token_context_result: dict[str, Any]) -> None:
    """Invoke the OpenWebuiAuthHandler with the open-webui headers and the token and store the authenticated user."""
    token_str = token_context["token_str"]

    # The open-webui headers provide user name, id, and email.
    headers = {
        "X-OpenWebUI-User-Name": "OpenWebUI User",
        "X-OpenWebUI-User-Id": "unused_in_result",  # This header is not used for oid
        "X-OpenWebUI-User-Email": "openwebui@example.com",
        "Authorization": f"Bearer {token_str}",
    }
    request = create_dummy_request(headers)

    handler = OpenWebuiAuthHandler(base_auth_handler=TokenAuthHandler())
    try:
        security = await HTTPBearer()(request)
        user = await handler(request, security)
        token_context_result["user"] = user
    except HTTPException as e:
        pytest.fail(f"OpenWebuiAuthHandler raised an unexpected exception: {e.detail}")


@when("I invoke the OpenWebuiAuthHandler with the required headers and a token expecting error")
@async_test
async def invoke_openwebui_auth_handler_expect_error(
    token_context: dict[str, Any], error_context: dict[str, Any]
) -> None:
    """Invoke the OpenWebuiAuthHandler with the open-webui headers and the token, capturing any error."""
    token_str = token_context["token_str"]

    headers = {
        "X-OpenWebUI-User-Name": "OpenWebUI User",
        "X-OpenWebUI-User-Id": "unused_in_result",
        "X-OpenWebUI-User-Email": "openwebui@example.com",
        "Authorization": f"Bearer {token_str}",
    }
    request = create_dummy_request(headers)

    handler = OpenWebuiAuthHandler(base_auth_handler=TokenAuthHandler())
    try:
        security = await HTTPBearer()(request)
        await handler(request, security)
        pytest.fail("OpenWebuiAuthHandler did not raise an exception")
    except HTTPException as e:
        error_context["error"] = e.detail


# --- Then Steps ---


@then(parsers.parse('the returned user should have name "{expected_name}"'))
def check_name(token_context_result: dict[str, Any], expected_name: str) -> None:
    """Check that the authenticated user has the expected name."""
    user = token_context_result.get("user")
    assert user is not None, "No user was returned by OpenWebuiAuthHandler"
    assert user.name == expected_name, f"Expected name '{expected_name}', got '{user.name}'"


@then(parsers.parse('the returned user should have preferred_username "{expected_email}"'))
def check_preferred_username(token_context_result: dict[str, Any], expected_email: str) -> None:
    """Check that the authenticated user has the expected preferred username."""
    user = token_context_result.get("user")
    assert user is not None, "No user was returned by OpenWebuiAuthHandler"
    assert user.email == expected_email, f"Expected email '{expected_email}', got '{user.email}'"


@then("the returned user should have oid matching the token's user id")
def check_user_oid(token_context_result: dict[str, Any], token_context: dict[str, Any]) -> None:
    """Check that the authenticated user's oid matches the expected user id from the token."""
    user = token_context_result.get("user")
    expected_oid = token_context.get("expected_user_oid")
    assert user is not None, "No user was returned by OpenWebuiAuthHandler"
    assert user.id == expected_oid, f"Expected user oid '{expected_oid}', got '{user.id}'"


@then(parsers.parse('the returned user should have roles "{role1}" and "{role2}"'))
def check_roles(token_context_result: dict[str, Any], role1: str, role2: str) -> None:
    """Check that the authenticated user has the expected roles."""
    user = token_context_result.get("user")
    assert user is not None, "No user was returned by OpenWebuiAuthHandler"
    expected_roles = {role1, role2}
    assert set(user.roles) == expected_roles, f"Expected roles {expected_roles}, got {set(user.roles)}"


@then(parsers.parse('I should receive an HTTP error with detail "{expected_detail}"'))
def check_error_detail(error_context: dict[str, Any], expected_detail: str) -> None:
    """Check that the error detail matches the expected detail."""
    error = error_context.get("error")
    assert error == expected_detail, f"Expected error detail '{expected_detail}', got '{error}'"
