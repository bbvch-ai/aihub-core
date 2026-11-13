"""Coverage for the user listing and existence check the LiteLLM user reconciliation relies on.

The reconciliation deletes a LiteLLM user once ``user_exists`` says Keycloak has no such user, so only a 404 may
read as absence: any other Keycloak failure must propagate rather than delete a user who still exists.
"""

from unittest.mock import AsyncMock

import pytest
from keycloak import KeycloakGetError

from swiss_ai_hub.core.auth.keycloak import keycloak_admin_service as kas_module
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService

pytestmark = pytest.mark.unit


@pytest.fixture
def patch_admin(monkeypatch: pytest.MonkeyPatch):
    def _apply(admin) -> None:
        monkeypatch.setattr(kas_module, "_create_admin", lambda: admin)

    return _apply


@pytest.mark.asyncio
async def test_existing_user_exists(patch_admin) -> None:
    admin = AsyncMock()
    admin.a_get_user = AsyncMock(return_value={"id": "user-1"})
    patch_admin(admin)

    assert await KeycloakAdminService.user_exists("user-1") is True


@pytest.mark.asyncio
async def test_a_404_means_the_user_does_not_exist(patch_admin) -> None:
    admin = AsyncMock()
    admin.a_get_user = AsyncMock(side_effect=KeycloakGetError(error_message="User not found", response_code=404))
    patch_admin(admin)

    assert await KeycloakAdminService.user_exists("gone") is False


@pytest.mark.asyncio
async def test_any_other_error_propagates_instead_of_reading_as_absence(patch_admin) -> None:
    admin = AsyncMock()
    admin.a_get_user = AsyncMock(side_effect=KeycloakGetError(error_message="Server error", response_code=500))
    patch_admin(admin)

    with pytest.raises(KeycloakGetError):
        await KeycloakAdminService.user_exists("user-1")


@pytest.mark.asyncio
async def test_every_user_is_listed_with_whether_they_are_enabled(patch_admin) -> None:
    """No `first` or `max` in the query, or python-keycloak returns a single page instead of all of them."""
    admin = AsyncMock()
    admin.a_get_users = AsyncMock(return_value=[{"id": "on", "enabled": True}, {"id": "off", "enabled": False}])
    patch_admin(admin)

    assert await KeycloakAdminService.get_enabled_by_user_id() == {"on": True, "off": False}
    query = admin.a_get_users.call_args.kwargs["query"]
    assert "first" not in query
    assert "max" not in query
