from collections.abc import Generator
from unittest.mock import AsyncMock

import pytest

from swiss_ai_hub.core.auth.keycloak import keycloak_admin_service as kas_module
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
from swiss_ai_hub.core.auth.keycloak.models.keycloak_user import KeycloakUser
from swiss_ai_hub.core.auth.superuser_settings import SuperuserSettings


@pytest.fixture(autouse=True)
def reset_superuser_cache() -> Generator[None]:
    kas_module._superuser_id_cache = None
    yield
    kas_module._superuser_id_cache = None


@pytest.mark.asyncio
async def test_get_superuser_id_returns_keycloak_user_id(monkeypatch: pytest.MonkeyPatch) -> None:
    expected_id = "superuser-keycloak-id"

    async def fake_find(email: str) -> KeycloakUser:
        assert email == SuperuserSettings().EMAIL
        return KeycloakUser(id=expected_id, email=email, username=email)

    monkeypatch.setattr(KeycloakAdminService, "find_user_by_email", fake_find)

    assert await KeycloakAdminService.get_superuser_id() == expected_id


@pytest.mark.asyncio
async def test_get_superuser_id_caches_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_find = AsyncMock(return_value=KeycloakUser(id="su-id", email="x@example.com", username="x"))
    monkeypatch.setattr(KeycloakAdminService, "find_user_by_email", mock_find)

    first = await KeycloakAdminService.get_superuser_id()
    second = await KeycloakAdminService.get_superuser_id()

    assert first == second == "su-id"
    assert mock_find.await_count == 1


@pytest.mark.asyncio
async def test_get_superuser_id_raises_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(KeycloakAdminService, "find_user_by_email", AsyncMock(return_value=None))

    with pytest.raises(RuntimeError, match="Superuser not found in Keycloak"):
        await KeycloakAdminService.get_superuser_id()


@pytest.mark.asyncio
async def test_assign_superuser_to_tenant_delegates_to_assign_user(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        KeycloakAdminService,
        "find_user_by_email",
        AsyncMock(return_value=KeycloakUser(id="su-id", email="x@example.com", username="x")),
    )
    mock_assign = AsyncMock(return_value=None)
    monkeypatch.setattr(KeycloakAdminService, "assign_user_to_tenant", mock_assign)

    await KeycloakAdminService.assign_superuser_to_tenant("tenant-x")

    mock_assign.assert_awaited_once_with("su-id", "tenant-x")
