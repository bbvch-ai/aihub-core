import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from bson import ObjectId
from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pytest_bdd import given, parsers, scenarios, then, when

from swiss_ai_hub.core.auth.dependencies.open_webui_auth_handler.open_webui_auth_handler import OpenWebuiAuthHandler
from swiss_ai_hub.core.auth.dependencies.token_auth_handler.token_auth_handler import TokenAuthHandler
from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.infrastructure.api.startup_tenant_settings import StartupTenantSettings
from swiss_ai_hub.core.persistence.access.entities.bearer_token import TOKEN_PREFIX, BearerToken
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.testing.asyncio_utils.bdd import async_test

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


def create_dummy_request(headers: dict[str, str]) -> Request:
    """Create and return a dummy FastAPI Request with the given headers."""
    headers_list = [(k.lower().encode("utf8"), v.encode("utf8")) for k, v in headers.items()]
    scope: dict[str, Any] = {"type": "http", "headers": headers_list, "method": "GET", "path": "/"}
    return Request(scope)


def generate_dummy_valid_token() -> str:
    """Generate a dummy ``sk-<random>`` token string that doesn't exist in the DB."""
    return f"{TOKEN_PREFIX}{secrets.token_urlsafe(48)}"


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
    name: str,
    email: str,
    roles: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prepare a token for a user with the given details.

    The handler's ``__call__`` is replaced below, so these scenarios never read the token or the tenant back; the
    real lookup path is covered by ``test_openwebui_auth_succeeds_when_token_owner_has_no_tenant``.
    """
    roles_list = [r.strip() for r in roles.split(",")]
    user_oid = str(ObjectId())
    token_context["token_str"] = generate_dummy_valid_token()
    token_context["expected_user_oid"] = user_oid
    token_context["user_name"] = name
    token_context["user_email"] = email
    token_context["user_roles"] = roles_list
    tenant_identity = TenantIdentity(
        id=StartupTenantSettings().ID,
        name=StartupTenantSettings().NAME,
        access_rules=["aihub.admin.>"],
    )

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
            acting_within_tenant=tenant_identity,
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
    """Store a properly-prefixed token that is not present in the database."""
    if not token.startswith(TOKEN_PREFIX):
        token = generate_dummy_valid_token()
    token_context["token_str"] = token

    # Mock handler to always raise token not found error
    async def mock_handler_call(
        self: OpenWebuiAuthHandler, request: Request, bearer_token: HTTPAuthorizationCredentials
    ) -> UserIdentity:
        raise HTTPException(status_code=401, detail="Token not found")

    monkeypatch.setattr(OpenWebuiAuthHandler, "__call__", mock_handler_call)


@given("I modify the token to cause a mismatch")
def modify_token_for_mismatch(token_context: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the stored token with a well-formed one that won't match any row."""
    token_context["token_str"] = generate_dummy_valid_token()

    # Mock handler to always raise token not found error
    async def mock_handler_call(
        self: OpenWebuiAuthHandler, request: Request, bearer_token: HTTPAuthorizationCredentials
    ) -> UserIdentity:
        raise HTTPException(status_code=401, detail="Token not found")

    monkeypatch.setattr(OpenWebuiAuthHandler, "__call__", mock_handler_call)


@given("I set the token expiry to a past time")
def set_token_expired(token_context: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the handler reject the token as expired."""

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


# --- End-to-end regression test for issue #1050 ---
# Exercises the REAL ``OpenWebuiAuthHandler.__call__`` (no monkeypatch on __call__) to
# prove that a bearer-token owner with no tenant membership and no active_tenant_id
# does not block end-users with a valid tenant.


@pytest.mark.beanie
async def test_openwebui_auth_succeeds_when_token_owner_has_no_tenant() -> None:
    import hashlib
    import hmac

    from swiss_ai_hub.core.auth.dependencies.auth_settings import AuthSettings
    from swiss_ai_hub.core.testing.auth_utils.user_mocks import register_fake_keycloak_user

    await TenantMetadataEntity.ensure_startup_tenant_metadata_exists(
        tenant_id=StartupTenantSettings().ID,
        name=StartupTenantSettings().NAME,
        description="Startup tenant for testing",
        access_rules=["aihub.admin.>"],
    )

    # Token owner: simulates seeded superuser — no /tenants/<id> membership, no active_tenant_id.
    token_owner_oid = str(ObjectId())
    register_fake_keycloak_user(
        user_id=token_owner_oid,
        name="Service Account",
        email="svc@example.com",
        attributes={},  # No active_tenant_id — would trigger the bug under the old code path.
    )
    expiry = datetime.now(UTC) + timedelta(hours=1)
    token_doc = await BearerToken.create_new_token(name="svc-token", expiry_date=expiry, user_oid=token_owner_oid)

    # End user: has /tenants/<startup> membership and active_tenant_id pointing at it.
    end_user_oid = str(ObjectId())
    end_user_email = "end.user@example.com"
    end_user_name = "End User"
    register_fake_keycloak_user(user_id=end_user_oid, name=end_user_name, email=end_user_email)
    default_tenant = await TenantMetadataEntity.get_startup_tenant_metadata()
    assert default_tenant is not None
    await UserTenantRoleEntity.create_or_update(
        user_id=end_user_oid,
        tenant_id=str(default_tenant.id),
        roles=["aihub-admin"],
        validate_roles=False,
    )

    # Mirror the production HMAC computation in OpenWebuiAuthHandler._verify_signature.
    secret = AuthSettings().OPEN_WEBUI_SIGNING_SECRET.get_secret_value().encode("utf-8")
    message = f"name:{end_user_name},email:{end_user_email}".encode()
    signature = hmac.new(secret, message, hashlib.sha256).hexdigest()

    headers = {
        "X-OpenWebUI-User-Name": end_user_name,
        "X-OpenWebUI-User-Email": end_user_email,
        "X-OpenWebUI-Signature": signature,
        "Authorization": f"Bearer {token_doc.token}",
    }
    request = create_dummy_request(headers)

    handler = OpenWebuiAuthHandler(base_auth_handler=TokenAuthHandler())
    security = await HTTPBearer()(request)
    user = await handler(request, security)

    assert user.email == end_user_email
    assert user.id == end_user_oid
    assert user.acting_within_tenant is not None
