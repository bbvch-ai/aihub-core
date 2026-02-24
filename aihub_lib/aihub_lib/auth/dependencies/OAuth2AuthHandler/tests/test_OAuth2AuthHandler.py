import base64
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2Settings import OAuth2Settings
from aihub_lib.persistence.user.UserEntity import UserEntity
from aihub_lib.testing.asyncio_utils.bdd import async_test
from aihub_lib.testing.auth_utils.oauth2_utils.oauth2_test_utils import (
    base64url_encode,
    generate_rsa_keypair,
    public_key_to_jwk,
)

# --- Scenario Declarations ---

scenarios("features/oauth2_auth_handler.feature")


# --- Database Mocking Fixture ---


@pytest.fixture(autouse=True)
def mock_database_operations(monkeypatch: pytest.MonkeyPatch):
    """Mock all database operations required by the auth handler."""
    from aihub_lib.auth.identity.TenantIdentity import TenantIdentity

    # Mock UserEntity.ensure_user_exists_for_auth
    def mock_ensure_user_exists(oid: str, name: str, email: str, profile_image: str | None = None) -> MagicMock:
        """Return a mock UserEntity with get_roles method."""
        user = MagicMock(spec=UserEntity)
        user.id = oid
        user.name = name
        user.email = email
        user.profile_image = profile_image
        user.last_updated = datetime(2025, 7, 4, 12, 14, 45, 185140, tzinfo=UTC)

        # Mock get_roles to return roles from token
        def mock_get_roles(_tenant_id: str) -> list[str]:
            # Roles are extracted from token and stored in UserEntity
            return getattr(user, "_roles", [])

        user.get_roles = mock_get_roles
        return user

    # Mock resolve_tenant_for_user to return a mock tenant identity
    def mock_resolve_tenant(_self, _request, _user_id: str) -> TenantIdentity:
        """Return a mock tenant identity."""
        return TenantIdentity(id="default-tenant-id", name="Default Tenant", access_rules=[])

    # Mock get_default_tenant_for_user (different signature - no request param)
    def mock_get_default_tenant(_self, _user_id: str) -> TenantIdentity:
        """Return a mock tenant identity for default tenant."""
        return TenantIdentity(id="default-tenant-id", name="Default Tenant", access_rules=[])

    # Apply monkeypatches
    monkeypatch.setattr(
        "aihub_lib.persistence.user.UserEntity.UserEntity.ensure_user_exists_for_auth", mock_ensure_user_exists
    )
    monkeypatch.setattr(
        "aihub_lib.auth.dependencies.AuthHandler.AuthHandler.resolve_tenant_for_user", mock_resolve_tenant
    )
    monkeypatch.setattr(
        "aihub_lib.auth.dependencies.AuthHandler.AuthHandler.get_default_tenant_for_user", mock_get_default_tenant
    )


# --- Fixtures ---


@pytest.fixture
def rsa_keys() -> dict[str, Any]:
    """Return a test RSA key pair with a fixed key ID and its JWK representation."""
    private_key, public_key = generate_rsa_keypair()
    kid = "test-key-id"
    jwk = public_key_to_jwk(public_key, kid)
    return {"private_key": private_key, "public_key": public_key, "kid": kid, "jwk": jwk}


@pytest.fixture
def fake_jwks_response(rsa_keys: dict[str, Any]) -> dict[str, Any]:
    """Return a fake JWKS response using the generated public key."""
    return {"keys": [rsa_keys["jwk"]]}


@pytest.fixture
def oauth2_context() -> dict[str, Any]:
    """Container for storing OAuth2-related data across steps."""
    return {}


# --- Given Steps ---


@given(
    parsers.parse('an OAuth2 configuration client_id "{client_id}", and authority_url "{authority_url}"'),
    target_fixture="oauth2_config",
)
def oauth2_config(monkeypatch: pytest.MonkeyPatch, client_id: str, authority_url: str) -> OAuth2Settings:
    """Set the OAuth2 configuration environment variables."""
    monkeypatch.setenv("OAUTH_CLIENT_ID", client_id)
    monkeypatch.setenv("OAUTH_AUTHORITY_URL", authority_url)
    return OAuth2Settings()


@given(
    parsers.parse('a valid OAuth2 token is generated with name "{name}", email "{email}", and roles "{roles}"'),
    target_fixture="generated_token",
)
def generated_token(
    monkeypatch: pytest.MonkeyPatch,
    oauth2_config: OAuth2Settings,
    rsa_keys: dict[str, Any],
    name: str,
    email: str,
    roles: str,
) -> str:
    """Generate a valid OAuth2 JWT with the specified claims."""
    now = datetime.now(UTC)
    exp = now + timedelta(minutes=10)

    monkeypatch.setenv("DANGEROUS_DEV_ONLY_AUTH_FAKE_NAME", name)
    monkeypatch.setenv("DANGEROUS_DEV_ONLY_AUTH_FAKE_EMAIL", email)
    monkeypatch.setenv("DANGEROUS_DEV_ONLY_AUTH_FAKE_OID", "test-oid")
    monkeypatch.setenv("DANGEROUS_DEV_ONLY_AUTH_FAKE_ROLES", roles)

    payload = {
        "name": name,
        "preferred_username": email,
        "roles": [r.strip() for r in roles.split(",")],
        "aud": oauth2_config.CLIENT_ID,
        "oid": "test-oid",
        "iss": f"{oauth2_config.AUTHORITY_URL}/v2.0",
        "exp": exp,
    }
    headers = {"kid": rsa_keys["kid"]}
    token: str = jwt.encode(payload, rsa_keys["private_key"], algorithm="RS256", headers=headers)
    return token


@given(parsers.parse('an invalid OAuth2 token "{token}"'))
def given_invalid_token(oauth2_context: dict[str, Any], token: str) -> None:
    """Store an invalid OAuth2 token in the context."""
    oauth2_context["token"] = token


@given(
    parsers.parse('an expired OAuth2 token is generated with name "{name}", email "{email}", and roles "{roles}"'),
    target_fixture="generated_token",
)
def generated_expired_token(
    monkeypatch: pytest.MonkeyPatch,
    oauth2_config: OAuth2Settings,
    rsa_keys: dict[str, Any],
    oauth2_context: dict[str, Any],
    name: str,
    email: str,
    roles: str,
) -> str:
    """Generate an expired OAuth2 JWT and store it in the context."""
    now = datetime.now(UTC)
    exp = now - timedelta(minutes=10)

    monkeypatch.setenv("DANGEROUS_DEV_ONLY_AUTH_FAKE_NAME", name)
    monkeypatch.setenv("DANGEROUS_DEV_ONLY_AUTH_FAKE_EMAIL", email)
    monkeypatch.setenv("DANGEROUS_DEV_ONLY_AUTH_FAKE_OID", "test-oid")
    monkeypatch.setenv("DANGEROUS_DEV_ONLY_AUTH_FAKE_ROLES", roles)

    payload = {
        "name": name,
        "preferred_username": email,
        "roles": [r.strip() for r in roles.split(",")],
        "aud": oauth2_config.CLIENT_ID,
        "oid": "expired-oid",
        "iss": f"{oauth2_config.AUTHORITY_URL}/v2.0",
        "exp": exp,
    }
    headers = {"kid": rsa_keys["kid"]}
    token: str = jwt.encode(payload, rsa_keys["private_key"], algorithm="RS256", headers=headers)
    oauth2_context["token"] = token
    return token


@given('I modify the token\'s header to use kid "unknown-key-id"')
def modify_token_unknown_kid(oauth2_context: dict[str, Any], generated_token: str) -> None:
    """Modify the generated token's header to use an unknown key ID."""
    parts = generated_token.split(".")
    if len(parts) != 3:
        pytest.fail("Token format invalid for modification")
    header_b64, payload_part, signature = parts
    header_bytes = base64.urlsafe_b64decode(header_b64 + "==")
    header = json.loads(header_bytes)
    header["kid"] = "unknown-key-id"
    new_header_b64 = base64url_encode(json.dumps(header).encode("utf-8"))
    new_token = ".".join([new_header_b64, payload_part, signature])
    oauth2_context["token"] = new_token


@given("I re-sign the token with a different private key")
def resign_token_with_different_key(
    oauth2_context: dict[str, Any], oauth2_config: OAuth2Settings, generated_token: str
) -> None:
    """Re-sign the token using a different RSA private key."""
    unverified = jwt.get_unverified_header(generated_token)
    payload = jwt.decode(generated_token, options={"verify_signature": False})
    new_private_key, _ = generate_rsa_keypair()
    new_token: str = jwt.encode(payload, new_private_key, algorithm="RS256", headers=unverified)
    oauth2_context["token"] = new_token


@given("no modification is applied to the token")
def store_generated_token(oauth2_context: dict[str, Any], generated_token: str) -> None:
    """Store the generated token in the context without modifications."""
    oauth2_context["token"] = generated_token


# --- When Steps ---


@when("I invoke the OAuth2AuthHandler with the token")
@async_test
async def invoke_oauth2_handler(
    monkeypatch: pytest.MonkeyPatch, oauth2_context: dict[str, Any], fake_jwks_response: dict[str, Any]
) -> None:
    """Invoke the OAuth2AuthHandler with the stored token and store the authenticated user."""
    from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2AuthHandler import OAuth2AuthHandler

    # Mock the method responsible for the external call
    monkeypatch.setattr(OAuth2AuthHandler, "_get_jwks", AsyncMock(return_value=fake_jwks_response))

    token = oauth2_context.get("token")
    if token is None:
        pytest.fail("No token found in context")
    token_str = token if isinstance(token, str) else token.decode("utf-8") if isinstance(token, bytes) else str(token)
    handler = OAuth2AuthHandler()
    user = await handler.authenticate_token(token_str, None)
    oauth2_context["user"] = user


@when("I invoke the OAuth2AuthHandler with the token expecting error")
@async_test
async def invoke_oauth2_handler_expect_error(
    monkeypatch: pytest.MonkeyPatch, oauth2_context: dict[str, Any], fake_jwks_response: dict[str, Any]
) -> None:
    """Invoke the OAuth2AuthHandler with the stored token and capture the error."""
    from aihub_lib.auth.dependencies.OAuth2AuthHandler.OAuth2AuthHandler import OAuth2AuthHandler

    # Mock the method responsible for the external call
    monkeypatch.setattr(OAuth2AuthHandler, "_get_jwks", AsyncMock(return_value=fake_jwks_response))

    token = oauth2_context.get("token")
    if token is None:
        pytest.fail("No token found in context")
    token_str = token if isinstance(token, str) else token.decode("utf-8") if isinstance(token, bytes) else str(token)
    handler = OAuth2AuthHandler()
    try:
        await handler.authenticate_token(token_str, None)
        pytest.fail("OAuth2AuthHandler did not raise an exception")
    except Exception as e:
        oauth2_context["error"] = str(e)


# --- Then Steps ---


@then(parsers.parse('the returned user should have name "{expected_name}"'))
def check_oauth2_user_name(oauth2_context: dict[str, Any], expected_name: str) -> None:
    """Check that the authenticated user has the expected name."""
    user = oauth2_context.get("user")
    assert user is not None, "No user was returned by OAuth2AuthHandler"
    assert user.name == expected_name, f'Expected name "{expected_name}", got "{user.name}"'


@then(parsers.parse('the returned user should have preferred_username "{expected_email}"'))
def check_oauth2_user_email(oauth2_context: dict[str, Any], expected_email: str) -> None:
    """Check that the authenticated user has the expected preferred username."""
    user = oauth2_context.get("user")
    assert user is not None, "No user was returned by OAuth2AuthHandler"
    assert user.email == expected_email, f'Expected email "{expected_email}", got "{user.email}"'


@then(parsers.parse('the returned user should have roles "{role1}" and "{role2}"'))
def check_oauth2_user_roles(oauth2_context: dict[str, Any], role1: str, role2: str) -> None:
    """Check that the authenticated user has the expected roles."""
    user = oauth2_context.get("user")
    assert user is not None, "No user was returned by OAuth2AuthHandler"
    assert set(user.roles) == {role1, role2}, f"Expected roles {{{role1}, {role2}}}, got {user.roles}"


@then(parsers.parse('I should receive an HTTP error with detail "{expected_detail}"'))
def check_oauth2_error(oauth2_context: dict[str, Any], expected_detail: str) -> None:
    """Check that the error message contains the expected detail."""
    error = oauth2_context.get("error")
    assert error is not None, "No error was captured"
    assert expected_detail in error, f'Expected error detail to contain "{expected_detail}", got "{error}"'
