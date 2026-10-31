import secrets
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from bson import ObjectId
from fastapi import HTTPException, Request
from fastapi.security import HTTPBearer

from swiss_ai_hub.core.auth.dependencies.token_auth_handler.token_auth_handler import TokenAuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.infrastructure.api.startup_tenant_settings import StartupTenantSettings
from swiss_ai_hub.core.persistence.access.entities.bearer_token import TOKEN_PREFIX, BearerToken
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.testing.auth_utils.user_mocks import register_fake_keycloak_user

pytestmark = pytest.mark.beanie


class SeededToken:
    """A token in the database, owned by a fake Keycloak user who is a member of the startup tenant."""

    def __init__(self, document: BearerToken, user_oid: str, tenant_id: str) -> None:
        self.document = document
        self.user_oid = user_oid
        self.tenant_id = tenant_id


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


def generate_dummy_valid_token() -> str:
    """Generate a dummy ``sk-<random>`` token string that doesn't exist in the DB."""
    return f"{TOKEN_PREFIX}{secrets.token_urlsafe(48)}"


async def seed_token(name: str, email: str, roles: list[str]) -> SeededToken:
    """Insert a token for a fake Keycloak user holding the given roles in the startup tenant."""
    default_tenant = await TenantMetadataEntity.ensure_startup_tenant_metadata_exists(
        tenant_id=StartupTenantSettings().ID,
        name=StartupTenantSettings().NAME,
        description="Startup tenant for testing",
        access_rules=["aihub.admin.>"],
    )
    user_oid = str(ObjectId())
    register_fake_keycloak_user(user_id=user_oid, name=name, email=email)
    await UserTenantRoleEntity.create_or_update(
        user_id=user_oid,
        tenant_id=str(default_tenant.id),
        roles=roles,
        validate_roles=False,
    )
    document = await BearerToken.create_new_token(
        name="token-name",
        expiry_date=datetime.now(UTC) + timedelta(hours=1),
        user_oid=user_oid,
    )
    return SeededToken(document, user_oid, str(default_tenant.id))


async def authenticate(token_str: str, tenant_id: str | None = None) -> UserIdentity:
    request = create_dummy_request(
        {"Authorization": f"Bearer {token_str}"},
        path_params={"tenant_id": tenant_id} if tenant_id else None,
    )
    security = await HTTPBearer()(request)
    return await TokenAuthHandler()(request, security)


async def rejection_detail(token_str: str) -> str:
    with pytest.raises(HTTPException) as excinfo:
        await authenticate(token_str)
    return excinfo.value.detail


@pytest_asyncio.fixture(loop_scope="session")
async def seeded_token(clean_beanie_collections: None) -> SeededToken:
    return await seed_token("Token User", "token@example.com", ["user", "editor"])


async def test_valid_token_returns_authenticated_user(seeded_token: SeededToken) -> None:
    user = await authenticate(seeded_token.document.token, seeded_token.tenant_id)

    assert user.name == "Token User"
    assert user.email == "token@example.com"
    assert user.id == seeded_token.user_oid
    assert set(user.roles) == {"user", "editor"}


async def test_token_with_invalid_format_is_rejected() -> None:
    assert await rejection_detail("not_a_valid_token") == "Malformed token: missing 'sk-' prefix"


async def test_token_not_found_in_database_is_rejected() -> None:
    detail = await rejection_detail(generate_dummy_valid_token())

    assert detail == "Unknown token: no matching row (revoked or never issued)"


async def test_modified_token_is_rejected_as_not_found(seeded_token: SeededToken) -> None:
    detail = await rejection_detail(generate_dummy_valid_token())

    assert detail == "Unknown token: no matching row (revoked or never issued)"


async def test_expired_token_is_rejected(seeded_token: SeededToken) -> None:
    seeded_token.document.expiry_date = datetime.now(UTC) - timedelta(hours=1)
    await seeded_token.document.save_changes()

    assert await rejection_detail(seeded_token.document.token) == "Expired token: expiry is in the past"


async def test_verify_token_returns_bearer_token_without_keycloak_or_tenant_resolution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``verify_token`` must NOT call Keycloak or tenant resolution — superuser tokens with no tenant must succeed."""
    fail = AsyncMock(side_effect=AssertionError("verify_token must not call Keycloak or tenant resolution"))
    monkeypatch.setattr(KeycloakAdminService, "get_user_by_id", fail)
    monkeypatch.setattr(KeycloakAdminService, "get_user_realm_roles", fail)
    monkeypatch.setattr(KeycloakAdminService, "get_active_tenant_id", fail)
    monkeypatch.setattr(KeycloakAdminService, "is_user_member_of_tenant", fail)

    user_oid = str(ObjectId())
    expiry = datetime.now(UTC) + timedelta(hours=1)
    token_doc = await BearerToken.create_new_token(name="svc-token", expiry_date=expiry, user_oid=user_oid)

    result = await TokenAuthHandler.verify_token(token_doc.token)

    assert result.user_oid == user_oid


async def test_verify_token_rejects_empty_token() -> None:
    with pytest.raises(HTTPException) as excinfo:
        await TokenAuthHandler.verify_token("")
    assert excinfo.value.status_code == 401


async def test_verify_token_rejects_unknown_token() -> None:
    with pytest.raises(HTTPException) as excinfo:
        await TokenAuthHandler.verify_token(generate_dummy_valid_token())
    assert excinfo.value.status_code == 401
