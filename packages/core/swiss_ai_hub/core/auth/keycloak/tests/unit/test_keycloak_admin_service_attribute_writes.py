from unittest.mock import AsyncMock, MagicMock

import pytest

from swiss_ai_hub.core.auth.keycloak import keycloak_admin_service as kas_module
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService

USER_ID = "user-1"


def _fake_admin(monkeypatch: pytest.MonkeyPatch, stored_user: dict) -> MagicMock:
    """Stands in for the KeycloakAdmin client, mirroring writes back into ``stored_user``."""

    async def a_get_user(user_id: str) -> dict:  # noqa: S7503
        return stored_user

    async def a_update_user(user_id: str, payload: dict) -> None:  # noqa: S7503
        stored_user.update(payload)

    admin = MagicMock()
    admin.a_get_user = AsyncMock(side_effect=a_get_user)
    admin.a_update_user = AsyncMock(side_effect=a_update_user)
    monkeypatch.setattr(kas_module, "_create_admin", lambda: admin)
    return admin


def _user(**attributes: list[str]) -> dict:
    return {"id": USER_ID, "username": "u@example.com", "email": "u@example.com", "attributes": dict(attributes)}


def _fake_redis() -> MagicMock:
    lock = MagicMock()
    lock.__aenter__ = AsyncMock(return_value=lock)
    lock.__aexit__ = AsyncMock(return_value=None)
    redis = MagicMock()
    redis.lock = MagicMock(return_value=lock)
    return redis


@pytest.mark.asyncio
async def test_locale_write_trims_duplicated_active_tenant(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keycloak rejects a resent single-valued attribute holding several values, failing the whole write."""
    stored_user = _user(active_tenant_id=["tenant-1", "tenant-1", "tenant-1"])
    _fake_admin(monkeypatch, stored_user)

    await KeycloakAdminService.set_preferred_locale(USER_ID, "en")

    assert stored_user["attributes"] == {"active_tenant_id": ["tenant-1"], "preferred_locale": ["en"]}


@pytest.mark.asyncio
async def test_set_active_tenant_replaces_duplicates_with_one_value(monkeypatch: pytest.MonkeyPatch) -> None:
    stored_user = _user(active_tenant_id=["tenant-1", "tenant-1"], preferred_locale=["de", "de"])
    _fake_admin(monkeypatch, stored_user)

    await KeycloakAdminService.set_active_tenant(USER_ID, "tenant-2")

    assert stored_user["attributes"] == {"active_tenant_id": ["tenant-2"], "preferred_locale": ["de"]}


@pytest.mark.asyncio
async def test_clear_active_tenant_removes_duplicated_attribute(monkeypatch: pytest.MonkeyPatch) -> None:
    stored_user = _user(active_tenant_id=["tenant-1", "tenant-1"], preferred_locale=["fr"])
    _fake_admin(monkeypatch, stored_user)

    await KeycloakAdminService.clear_active_tenant(USER_ID)

    assert stored_user["attributes"] == {"preferred_locale": ["fr"]}


@pytest.mark.asyncio
async def test_ensure_active_tenant_skips_lock_when_current_tenant_is_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    """The auth hot path must not take a Redis lock on every request."""
    monkeypatch.setattr(KeycloakAdminService, "_tenant_to_auto_select", AsyncMock(return_value=None))
    set_active_tenant = AsyncMock()
    monkeypatch.setattr(KeycloakAdminService, "set_active_tenant", set_active_tenant)
    redis = _fake_redis()

    await KeycloakAdminService.ensure_active_tenant(USER_ID, redis)

    redis.lock.assert_not_called()
    set_active_tenant.assert_not_awaited()


@pytest.mark.asyncio
async def test_ensure_active_tenant_writes_under_per_user_lock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(KeycloakAdminService, "_tenant_to_auto_select", AsyncMock(return_value="tenant-1"))
    set_active_tenant = AsyncMock()
    monkeypatch.setattr(KeycloakAdminService, "set_active_tenant", set_active_tenant)
    redis = _fake_redis()

    await KeycloakAdminService.ensure_active_tenant(USER_ID, redis)

    assert redis.lock.call_args.args[0] == f"keycloak:active-tenant:{USER_ID}"
    set_active_tenant.assert_awaited_once_with(USER_ID, "tenant-1")


@pytest.mark.asyncio
async def test_ensure_active_tenant_skips_write_when_set_while_waiting_for_lock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A caller that waited for the lock must not rewrite what the holder just set."""
    monkeypatch.setattr(KeycloakAdminService, "_tenant_to_auto_select", AsyncMock(side_effect=["tenant-1", None]))
    set_active_tenant = AsyncMock()
    monkeypatch.setattr(KeycloakAdminService, "set_active_tenant", set_active_tenant)

    await KeycloakAdminService.ensure_active_tenant(USER_ID, _fake_redis())

    set_active_tenant.assert_not_awaited()


@pytest.mark.asyncio
async def test_ensure_active_tenant_without_redis_writes_directly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(KeycloakAdminService, "_tenant_to_auto_select", AsyncMock(return_value="tenant-1"))
    set_active_tenant = AsyncMock()
    monkeypatch.setattr(KeycloakAdminService, "set_active_tenant", set_active_tenant)

    await KeycloakAdminService.ensure_active_tenant(USER_ID, None)

    set_active_tenant.assert_awaited_once_with(USER_ID, "tenant-1")
