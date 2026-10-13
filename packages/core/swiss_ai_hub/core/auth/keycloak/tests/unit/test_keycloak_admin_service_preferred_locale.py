from unittest.mock import AsyncMock, MagicMock

import pytest

from swiss_ai_hub.core.auth.keycloak import keycloak_admin_service as kas_module
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService

USER_ID = "user-1"


def _fake_admin(monkeypatch: pytest.MonkeyPatch, stored_user: dict) -> MagicMock:
    """Stands in for the KeycloakAdmin client, mirroring writes back into ``stored_user``."""

    async def a_get_user(user_id: str) -> dict:  # noqa: S7503
        assert user_id == USER_ID
        return stored_user

    async def a_update_user(user_id: str, payload: dict) -> None:  # noqa: S7503
        assert user_id == USER_ID
        stored_user.update(payload)

    admin = MagicMock()
    admin.a_get_user = AsyncMock(side_effect=a_get_user)
    admin.a_update_user = AsyncMock(side_effect=a_update_user)
    monkeypatch.setattr(kas_module, "_create_admin", lambda: admin)
    return admin


def _user(**attributes: list[str]) -> dict:
    return {"id": USER_ID, "username": "u@example.com", "email": "u@example.com", "attributes": dict(attributes)}


@pytest.mark.asyncio
async def test_get_preferred_locale_returns_stored_value(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_admin(monkeypatch, _user(preferred_locale=["fr"]))

    assert await KeycloakAdminService.get_preferred_locale(USER_ID) == "fr"


@pytest.mark.asyncio
async def test_get_preferred_locale_returns_none_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_admin(monkeypatch, _user(active_tenant_id=["tenant-1"]))

    assert await KeycloakAdminService.get_preferred_locale(USER_ID) is None


@pytest.mark.asyncio
async def test_set_preferred_locale_round_trips(monkeypatch: pytest.MonkeyPatch) -> None:
    stored_user = _user()
    _fake_admin(monkeypatch, stored_user)

    await KeycloakAdminService.set_preferred_locale(USER_ID, "it")

    assert stored_user["attributes"]["preferred_locale"] == ["it"]
    assert await KeycloakAdminService.get_preferred_locale(USER_ID) == "it"


@pytest.mark.asyncio
async def test_set_preferred_locale_preserves_other_attributes(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET-merge-PUT, not overwrite: the active tenant must survive a language change."""
    stored_user = _user(active_tenant_id=["tenant-1"])
    _fake_admin(monkeypatch, stored_user)

    await KeycloakAdminService.set_preferred_locale(USER_ID, "en")

    assert stored_user["attributes"] == {"active_tenant_id": ["tenant-1"], "preferred_locale": ["en"]}


@pytest.mark.asyncio
async def test_set_preferred_locale_overwrites_previous_choice(monkeypatch: pytest.MonkeyPatch) -> None:
    stored_user = _user(preferred_locale=["de"])
    _fake_admin(monkeypatch, stored_user)

    await KeycloakAdminService.set_preferred_locale(USER_ID, "en")

    assert stored_user["attributes"]["preferred_locale"] == ["en"]
