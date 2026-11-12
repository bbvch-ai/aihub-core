from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import pytest
from fastapi import HTTPException

from swiss_ai_hub.core.auth.dependencies.keycloak_auth_handler.keycloak_auth_handler import KeycloakAuthHandler
from swiss_ai_hub.core.auth.forwarded_token.forwarded_user_token_verifier import ForwardedUserTokenVerifier
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.auth.keycloak.keycloak_settings import KeycloakSettings
from swiss_ai_hub.core.testing.auth_utils.oauth2_utils.oauth2_test_utils import generate_rsa_keypair
from swiss_ai_hub.core.testing.auth_utils.test_identity import TEST_USER_OID, fake_user

KID = "forwarded-token-test-key"


@pytest.fixture
def keycloak_env(monkeypatch: pytest.MonkeyPatch) -> KeycloakSettings:
    monkeypatch.setenv("KEYCLOAK_URL", "http://keycloak.test")
    monkeypatch.setenv("KEYCLOAK_REALM", "aihub")
    monkeypatch.delenv("KEYCLOAK_EXTERNAL_URL", raising=False)
    return KeycloakSettings()


@pytest.fixture
def signing_key(monkeypatch: pytest.MonkeyPatch, keycloak_env: KeycloakSettings) -> Generator[Any]:
    private_key, public_key = generate_rsa_keypair()
    KeycloakAuthHandler._rsa_key_cache.clear()
    KeycloakAuthHandler._rsa_key_cache[KID] = public_key
    yield private_key
    KeycloakAuthHandler._rsa_key_cache.clear()


@pytest.fixture
def no_keycloak_side_effects(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    calls: list[str] = []

    async def record_ensure_active_tenant(*_: object) -> None:
        calls.append("ensure_active_tenant")

    def record_sync(*_: object) -> None:
        calls.append("sync_tenant_memberships")

    monkeypatch.setattr(KeycloakAdminService, "ensure_active_tenant", staticmethod(record_ensure_active_tenant))
    monkeypatch.setattr(KeycloakAuthHandler, "_sync_tenant_memberships", staticmethod(record_sync))
    return calls


def _token(private_key: Any, settings: KeycloakSettings, **overrides: Any) -> str:
    claims: dict[str, Any] = {
        "sub": TEST_USER_OID,
        "aud": "account",
        "iss": settings.ISSUER_URL,
        "exp": datetime.now(UTC) + timedelta(minutes=10),
    }
    claims.update(overrides)
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": KID})


@pytest.mark.asyncio
async def test_headers_without_a_user_token_pass_through_unchecked() -> None:
    headers = await ForwardedUserTokenVerifier.verified_aihub_headers(
        {"X-AIHub-Anonymise": "true", "Authorization": "Bearer sk-shared"}, fake_user()
    )

    assert headers == {"x-aihub-anonymise": "true"}


@pytest.mark.asyncio
async def test_the_requesting_users_own_token_is_forwarded(signing_key: Any, keycloak_env: KeycloakSettings) -> None:
    token = _token(signing_key, keycloak_env)

    headers = await ForwardedUserTokenVerifier.verified_aihub_headers({"X-AIHub-User-Token": token}, fake_user())

    assert headers == {"x-aihub-user-token": token}


@pytest.mark.asyncio
async def test_another_users_token_is_refused_without_echoing_it(
    signing_key: Any, keycloak_env: KeycloakSettings
) -> None:
    token = _token(signing_key, keycloak_env, sub="someone-else")

    with pytest.raises(HTTPException) as refused:
        await ForwardedUserTokenVerifier.verified_aihub_headers({"X-AIHub-User-Token": token}, fake_user())

    assert refused.value.status_code == 401
    assert token not in str(refused.value.detail)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"exp": datetime.now(UTC) - timedelta(minutes=1)}, id="expired"),
        pytest.param({"iss": "http://another-keycloak/realms/aihub"}, id="other-issuer"),
    ],
)
async def test_a_token_keycloak_would_not_accept_is_refused(
    signing_key: Any, keycloak_env: KeycloakSettings, overrides: dict[str, Any]
) -> None:
    token = _token(signing_key, keycloak_env, **overrides)

    with pytest.raises(HTTPException) as refused:
        await ForwardedUserTokenVerifier.verified_aihub_headers({"X-AIHub-User-Token": token}, fake_user())

    assert refused.value.status_code == 401


@pytest.mark.asyncio
async def test_an_openwebui_token_without_an_audience_is_accepted(
    signing_key: Any, keycloak_env: KeycloakSettings
) -> None:
    """OpenWebUI's Keycloak client issues tokens with no ``aud`` claim, only ``azp``."""
    claims = {"sub": TEST_USER_OID, "iss": keycloak_env.ISSUER_URL, "azp": "openwebui"}
    claims["exp"] = datetime.now(UTC) + timedelta(minutes=10)
    token = jwt.encode(claims, signing_key, algorithm="RS256", headers={"kid": KID})

    headers = await ForwardedUserTokenVerifier.verified_aihub_headers({"X-AIHub-User-Token": token}, fake_user())

    assert headers == {"x-aihub-user-token": token}


@pytest.mark.asyncio
async def test_api_login_still_requires_the_account_audience(signing_key: Any, keycloak_env: KeycloakSettings) -> None:
    token = _token(signing_key, keycloak_env, aud="some-other-service")

    with pytest.raises(HTTPException) as refused:
        await KeycloakAuthHandler().decode_token(token)

    assert refused.value.status_code == 401


@pytest.mark.asyncio
async def test_a_token_signed_by_another_key_is_refused(keycloak_env: KeycloakSettings, signing_key: Any) -> None:
    foreign_key, _ = generate_rsa_keypair()
    token = _token(foreign_key, keycloak_env)

    with pytest.raises(HTTPException) as refused:
        await ForwardedUserTokenVerifier.verified_aihub_headers({"X-AIHub-User-Token": token}, fake_user())

    assert refused.value.status_code == 401


@pytest.mark.asyncio
async def test_decoding_a_token_changes_no_tenant_state(
    signing_key: Any, keycloak_env: KeycloakSettings, no_keycloak_side_effects: list[str]
) -> None:
    claims = await KeycloakAuthHandler().decode_token(_token(signing_key, keycloak_env))

    assert claims["sub"] == TEST_USER_OID
    assert no_keycloak_side_effects == []
