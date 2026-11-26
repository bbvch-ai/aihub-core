import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import jwt
import pytest
from fastapi import HTTPException, Request

from swiss_ai_hub.core.auth.dependencies.open_webui_session_auth_handler.open_webui_session_auth_handler import (
    OpenWebuiSessionAuthHandler,
)
from swiss_ai_hub.core.auth.identity.tenant_identity import TenantIdentity
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.auth.keycloak.models.keycloak_user import KeycloakUser
from swiss_ai_hub.core.auth.realm_roles import SYS_ADMIN_ROLE

pytestmark = pytest.mark.unit

TENANT_ID = "tenant-1"
EMAIL = "ada@example.com"
SECRET = "openwebui-signing-secret-of-at-least-32-bytes"
KEYCLOAK_USER = KeycloakUser(id="kc-1", username="ada", firstName="Ada", lastName="Lovelace", email=EMAIL)


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def set(self, key: str, value: str, ex: int) -> None:
        self.values[key] = value


def _token(secret: str = SECRET, expires_in: int = 3600) -> str:
    return jwt.encode({"id": "owui-1", "exp": int(time.time()) + expires_in}, secret, algorithm="HS256")


def _request(cookie: str | None, redis: FakeRedis) -> Request:
    headers = [(b"cookie", cookie.encode())] if cookie else []
    app = SimpleNamespace(state=SimpleNamespace(redis=redis))
    return Request({"type": "http", "headers": headers, "path_params": {"tenant_id": TENANT_ID}, "app": app})


def _identity() -> UserIdentity:
    tenant = TenantIdentity(id=TENANT_ID, name="Tenant", access_rules=["aihub.user.>"])
    return UserIdentity(id=KEYCLOAK_USER.id, name="Ada Lovelace", email=EMAIL, roles=[], acting_within_tenant=tenant)


def _handler(email: str | None) -> tuple[OpenWebuiSessionAuthHandler, AsyncMock]:
    lookup = SimpleNamespace(email_of=AsyncMock(return_value=email))
    return OpenWebuiSessionAuthHandler(session_lookup=lookup, secret_key=SECRET), lookup.email_of


@pytest.fixture
def keycloak() -> SimpleNamespace:
    with (
        patch.object(KeycloakAdminService, "find_user_by_email", AsyncMock(return_value=KEYCLOAK_USER)) as find,
        patch.object(KeycloakAdminService, "get_user_realm_roles", AsyncMock(return_value=[])) as roles,
    ):
        yield SimpleNamespace(find=find, roles=roles)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "cookie",
    [
        None,
        "other=1",
        "token=sk-api-key",
        "token=not-a-jwt",
        f"token={_token(secret='another-secret-of-at-least-thirty-two-bytes')}",
        f"token={_token(expires_in=-60)}",
        f"token={'a' * 5000}",
    ],
)
async def test_should_reject_without_asking_openwebui_when_the_cookie_is_no_valid_session(cookie: str | None) -> None:
    handler, email_of = _handler(EMAIL)
    redis = FakeRedis()

    with pytest.raises(HTTPException) as error:
        await handler(_request(cookie, redis))

    assert error.value.status_code == 401
    email_of.assert_not_awaited()
    assert redis.values == {}


@pytest.mark.asyncio
async def test_should_reject_and_remember_when_openwebui_rejects_the_session(keycloak: SimpleNamespace) -> None:
    handler, email_of = _handler(None)
    redis = FakeRedis()
    cookie = f"token={_token()}"

    for _ in range(2):
        with pytest.raises(HTTPException) as error:
            await handler(_request(cookie, redis))
        assert error.value.status_code == 401

    email_of.assert_awaited_once()
    keycloak.find.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("keycloak_user", [None, KEYCLOAK_USER.model_copy(update={"enabled": False})])
async def test_should_reject_when_the_session_email_has_no_enabled_keycloak_user(
    keycloak: SimpleNamespace, keycloak_user: KeycloakUser | None
) -> None:
    keycloak.find.return_value = keycloak_user
    handler, _ = _handler(EMAIL)

    with pytest.raises(HTTPException) as error:
        await handler(_request(f"token={_token()}", FakeRedis()))

    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_should_build_the_identity_in_the_path_tenant_and_cache_it(keycloak: SimpleNamespace) -> None:
    handler, email_of = _handler(EMAIL)
    redis = FakeRedis()
    token = _token()

    with patch.object(handler, "build_identity", AsyncMock(return_value=_identity())) as build_identity:
        first = await handler(_request(f"token={token}", redis))
        second = await handler(_request(f"token={token}", redis))

    assert first == second == _identity()
    email_of.assert_awaited_once_with(token)
    build_identity.assert_awaited_once()
    assert build_identity.await_args.kwargs["request"].path_params["tenant_id"] == TENANT_ID
    assert not any(token in key for key in redis.values)


@pytest.mark.asyncio
async def test_should_mark_a_sysadmin_without_granting_the_sysadmin_bypass(keycloak: SimpleNamespace) -> None:
    keycloak.roles.return_value = [SYS_ADMIN_ROLE]
    handler, _ = _handler(EMAIL)

    with patch.object(handler, "build_identity", AsyncMock(return_value=_identity())) as build_identity:
        await handler(_request(f"token={_token()}", FakeRedis()))

    assert build_identity.await_args.kwargs["openwebui_sys_admin"] is True
    assert "is_sys_admin" not in build_identity.await_args.kwargs
