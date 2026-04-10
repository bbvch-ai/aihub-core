import base64
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest
from fastapi import HTTPException
from pytest_bdd import given, parsers, scenarios, then, when

from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.dependencies.keycloak_auth_handler.keycloak_auth_handler import KeycloakAuthHandler
from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.keycloak.keycloak_settings import KeycloakSettings
from swiss_ai_hub.core.testing.asyncio_utils.bdd import async_test
from swiss_ai_hub.core.testing.auth_utils.oauth2_utils.oauth2_test_utils import (
    base64url_encode,
    generate_rsa_keypair,
    public_key_to_jwk,
)

scenarios("features/keycloak_auth_handler.feature")


# --- Cache Cleanup Fixture ---


@pytest.fixture(autouse=True)
def clear_handler_caches():
    """Clear class-level JWKS and RSA key caches between tests."""
    from swiss_ai_hub.core.auth.dependencies.keycloak_auth_handler.keycloak_auth_handler import KeycloakAuthHandler

    KeycloakAuthHandler._jwks_cache.clear()
    KeycloakAuthHandler._rsa_key_cache.clear()
    yield
    KeycloakAuthHandler._jwks_cache.clear()
    KeycloakAuthHandler._rsa_key_cache.clear()


# --- Database Mocking Fixture ---


@pytest.fixture(autouse=True)
def mock_database_operations(monkeypatch: pytest.MonkeyPatch):
    """Mock database and identity operations required by the auth handler."""

    async def mock_get_default_tenant(user_id: str) -> TenantIdentity:
        tenant = MagicMock(spec=TenantIdentity)
        tenant.id = "default-tenant"
        tenant.name = "Default"
        return tenant

    async def mock_sync_tenant_memberships(user_id: str, tenants_claim: list[str]) -> None:
        pass

    def mock_get_roles(user_id: str, tenant_id: str) -> list[str]:
        return []

    monkeypatch.setattr(
        "swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity.UserTenantRoleEntity.get_roles_for_user_in_tenant",
        mock_get_roles,
    )
    monkeypatch.setattr(AuthHandler, "get_active_tenant_for_user", staticmethod(mock_get_default_tenant))
    monkeypatch.setattr(KeycloakAuthHandler, "_sync_tenant_memberships", staticmethod(mock_sync_tenant_memberships))


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
def keycloak_context() -> dict[str, Any]:
    """Container for storing Keycloak-related data across steps."""
    return {}


# --- Given Steps ---


@given(
    parsers.parse('a Keycloak configuration with url "{url}" and realm "{realm}"'),
    target_fixture="keycloak_config",
)
def keycloak_config(monkeypatch: pytest.MonkeyPatch, url: str, realm: str) -> KeycloakSettings:
    """Set the Keycloak configuration environment variables."""
    monkeypatch.setenv("KEYCLOAK_URL", url)
    monkeypatch.setenv("KEYCLOAK_REALM", realm)
    return KeycloakSettings()


@given(
    parsers.parse('a valid Keycloak token is generated with name "{name}", email "{email}", and sub "{sub}"'),
    target_fixture="generated_token",
)
def generated_token(
    keycloak_config: KeycloakSettings,
    keycloak_context: dict[str, Any],
    rsa_keys: dict[str, Any],
    name: str,
    email: str,
    sub: str,
) -> str:
    """Generate a valid Keycloak JWT with the specified claims."""
    now = datetime.now(UTC)
    exp = now + timedelta(minutes=10)

    payload = {
        "sub": sub,
        "name": name,
        "email": email,
        "aud": "account",
        "iss": keycloak_config.ISSUER_URL,
        "exp": exp,
    }
    headers = {"kid": rsa_keys["kid"]}
    token: str = jwt.encode(payload, rsa_keys["private_key"], algorithm="RS256", headers=headers)
    keycloak_context["token"] = token
    return token


@given("a Keycloak token without kid in the header")
def token_without_kid(
    keycloak_config: KeycloakSettings,
    keycloak_context: dict[str, Any],
    rsa_keys: dict[str, Any],
) -> None:
    """Generate a token without a kid in the header."""
    now = datetime.now(UTC)
    exp = now + timedelta(minutes=10)

    payload = {
        "sub": "no-kid-sub",
        "name": "No Kid",
        "email": "nokid@example.com",
        "aud": "account",
        "iss": keycloak_config.ISSUER_URL,
        "exp": exp,
    }
    token: str = jwt.encode(payload, rsa_keys["private_key"], algorithm="RS256")
    keycloak_context["token"] = token


@given(
    parsers.parse('an expired Keycloak token is generated with name "{name}", email "{email}", and sub "{sub}"'),
    target_fixture="generated_token",
)
def generated_expired_token(
    keycloak_config: KeycloakSettings,
    keycloak_context: dict[str, Any],
    rsa_keys: dict[str, Any],
    name: str,
    email: str,
    sub: str,
) -> str:
    """Generate an expired Keycloak JWT."""
    now = datetime.now(UTC)
    exp = now - timedelta(minutes=10)

    payload = {
        "sub": sub,
        "name": name,
        "email": email,
        "aud": "account",
        "iss": keycloak_config.ISSUER_URL,
        "exp": exp,
    }
    headers = {"kid": rsa_keys["kid"]}
    token: str = jwt.encode(payload, rsa_keys["private_key"], algorithm="RS256", headers=headers)
    keycloak_context["token"] = token
    return token


@given(parsers.parse('the token header kid is changed to "{new_kid}"'))
def modify_token_kid(keycloak_context: dict[str, Any], generated_token: str, new_kid: str) -> None:
    """Modify the generated token's header to use a different key ID."""
    parts = generated_token.split(".")
    if len(parts) != 3:
        pytest.fail("Token format invalid for modification")
    header_b64, payload_part, signature = parts
    header_bytes = base64.urlsafe_b64decode(header_b64 + "==")
    header = json.loads(header_bytes)
    header["kid"] = new_kid
    new_header_b64 = base64url_encode(json.dumps(header).encode("utf-8"))
    keycloak_context["token"] = ".".join([new_header_b64, payload_part, signature])


@given("the token is re-signed with a different private key")
def resign_token_with_different_key(
    keycloak_context: dict[str, Any],
    keycloak_config: KeycloakSettings,
    generated_token: str,
) -> None:
    """Re-sign the token using a different RSA private key."""
    unverified = jwt.get_unverified_header(generated_token)
    payload = jwt.decode(generated_token, options={"verify_signature": False})
    new_private_key, _ = generate_rsa_keypair()
    new_token: str = jwt.encode(payload, new_private_key, algorithm="RS256", headers=unverified)
    keycloak_context["token"] = new_token


@given(parsers.parse('a Keycloak token with wrong issuer "{wrong_issuer}"'))
def token_with_wrong_issuer(
    keycloak_config: KeycloakSettings,
    keycloak_context: dict[str, Any],
    rsa_keys: dict[str, Any],
    wrong_issuer: str,
) -> None:
    """Generate a token with an incorrect issuer claim."""
    now = datetime.now(UTC)
    exp = now + timedelta(minutes=10)

    payload = {
        "sub": "wrong-issuer-sub",
        "name": "Wrong Issuer",
        "email": "wrongissuer@example.com",
        "aud": "account",
        "iss": wrong_issuer,
        "exp": exp,
    }
    headers = {"kid": rsa_keys["kid"]}
    token: str = jwt.encode(payload, rsa_keys["private_key"], algorithm="RS256", headers=headers)
    keycloak_context["token"] = token


@given(parsers.parse('a Keycloak token with wrong audience "{wrong_audience}"'))
def token_with_wrong_audience(
    keycloak_config: KeycloakSettings,
    keycloak_context: dict[str, Any],
    rsa_keys: dict[str, Any],
    wrong_audience: str,
) -> None:
    """Generate a token with an incorrect audience claim."""
    now = datetime.now(UTC)
    exp = now + timedelta(minutes=10)

    payload = {
        "sub": "wrong-audience-sub",
        "name": "Wrong Audience",
        "email": "wrongaudience@example.com",
        "aud": wrong_audience,
        "iss": keycloak_config.ISSUER_URL,
        "exp": exp,
    }
    headers = {"kid": rsa_keys["kid"]}
    token: str = jwt.encode(payload, rsa_keys["private_key"], algorithm="RS256", headers=headers)
    keycloak_context["token"] = token


@given("the JWKS endpoint is unavailable")
def jwks_unavailable(keycloak_context: dict[str, Any]) -> None:
    """Flag that the JWKS endpoint should simulate a failure."""
    keycloak_context["jwks_unavailable"] = True


@given(parsers.parse('an invalid Keycloak token "{token}"'))
def given_invalid_token(keycloak_context: dict[str, Any], token: str) -> None:
    """Store an invalid Keycloak token in the context."""
    keycloak_context["token"] = token


# --- When Steps ---


@when("I invoke the KeycloakAuthHandler with the token")
@async_test
async def invoke_keycloak_handler(
    monkeypatch: pytest.MonkeyPatch,
    keycloak_context: dict[str, Any],
    fake_jwks_response: dict[str, Any],
) -> None:
    """Invoke the KeycloakAuthHandler with the stored token and store the authenticated user."""
    from swiss_ai_hub.core.auth.dependencies.keycloak_auth_handler.keycloak_auth_handler import KeycloakAuthHandler

    monkeypatch.setattr(KeycloakAuthHandler, "_get_jwks", AsyncMock(return_value=fake_jwks_response))

    token = keycloak_context.get("token")
    if token is None:
        pytest.fail("No token found in context")
    handler = KeycloakAuthHandler()
    user = await handler.authenticate_token(token)
    keycloak_context["user"] = user


@when("I invoke the KeycloakAuthHandler with the token expecting error")
@async_test
async def invoke_keycloak_handler_expect_error(
    monkeypatch: pytest.MonkeyPatch,
    keycloak_context: dict[str, Any],
    fake_jwks_response: dict[str, Any],
) -> None:
    """Invoke the KeycloakAuthHandler with the stored token and capture the error."""
    from swiss_ai_hub.core.auth.dependencies.keycloak_auth_handler.keycloak_auth_handler import KeycloakAuthHandler

    if keycloak_context.get("jwks_unavailable"):
        monkeypatch.setattr(
            KeycloakAuthHandler,
            "_get_jwks",
            AsyncMock(side_effect=HTTPException(status_code=500, detail="Authentication service unavailable")),
        )
    else:
        monkeypatch.setattr(KeycloakAuthHandler, "_get_jwks", AsyncMock(return_value=fake_jwks_response))

    token = keycloak_context.get("token")
    if token is None:
        pytest.fail("No token found in context")
    handler = KeycloakAuthHandler()
    try:
        await handler.authenticate_token(token)
        pytest.fail("KeycloakAuthHandler did not raise an exception")
    except Exception as e:
        keycloak_context["error"] = str(e)


# --- Then Steps ---


@then(parsers.parse('the returned user should have name "{expected_name}"'))
def check_user_name(keycloak_context: dict[str, Any], expected_name: str) -> None:
    """Check that the authenticated user has the expected name."""
    user = keycloak_context.get("user")
    assert user is not None, "No user was returned by KeycloakAuthHandler"
    assert user.name == expected_name, f'Expected name "{expected_name}", got "{user.name}"'


@then(parsers.parse('the returned user should have email "{expected_email}"'))
def check_user_email(keycloak_context: dict[str, Any], expected_email: str) -> None:
    """Check that the authenticated user has the expected email."""
    user = keycloak_context.get("user")
    assert user is not None, "No user was returned by KeycloakAuthHandler"
    assert user.email == expected_email, f'Expected email "{expected_email}", got "{user.email}"'


@then(parsers.parse('I should receive an HTTP error with detail "{expected_detail}"'))
def check_error(keycloak_context: dict[str, Any], expected_detail: str) -> None:
    """Check that the error message contains the expected detail."""
    error = keycloak_context.get("error")
    assert error is not None, "No error was captured"
    assert expected_detail in error, f'Expected error detail to contain "{expected_detail}", got "{error}"'
