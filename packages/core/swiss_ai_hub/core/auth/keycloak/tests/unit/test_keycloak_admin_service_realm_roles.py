"""Coverage for ``KeycloakAdminService.get_user_realm_roles``.

The service is how every auth handler derives the sysadmin flag (see
``TokenAuthHandler``, ``KeycloakAuthHandler``), so its fallback behavior on
Keycloak errors is a privilege-escalation-prevention concern: a transient
Keycloak failure must not elevate *or* strand a token holder.
"""

from unittest.mock import AsyncMock

import pytest
from keycloak import KeycloakGetError

from swiss_ai_hub.core.auth.keycloak import keycloak_admin_service as kas_module
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService


@pytest.fixture
def patch_admin(monkeypatch: pytest.MonkeyPatch):
    """Returns a helper that installs a fake ``KeycloakAdmin`` for a single test.

    Uses the module-level ``_create_admin`` factory so every
    ``KeycloakAdminService`` method routes through the fake — matches the wiring
    used by the session-scoped autouse mock in ``user_mocks``.
    """

    def _apply(admin) -> None:
        monkeypatch.setattr(kas_module, "_create_admin", lambda: admin)

    return _apply


@pytest.mark.asyncio
async def test_returns_role_names(patch_admin) -> None:
    admin = AsyncMock()
    admin.a_get_realm_roles_of_user = AsyncMock(
        return_value=[
            {"name": "AIHubSysAdmin", "id": "1"},
            {"name": "AIHubUser", "id": "2"},
        ]
    )
    patch_admin(admin)

    assert await KeycloakAdminService.get_user_realm_roles("user-1") == ["AIHubSysAdmin", "AIHubUser"]


@pytest.mark.asyncio
async def test_drops_entries_without_a_name(patch_admin) -> None:
    """Malformed role rows from Keycloak must be skipped rather than producing empty strings."""
    admin = AsyncMock()
    admin.a_get_realm_roles_of_user = AsyncMock(
        return_value=[{"name": "AIHubSysAdmin"}, {"id": "no-name"}, {"name": ""}]
    )
    patch_admin(admin)

    assert await KeycloakAdminService.get_user_realm_roles("user-1") == ["AIHubSysAdmin"]


@pytest.mark.asyncio
async def test_returns_empty_list_when_keycloak_raises_get_error(patch_admin) -> None:
    """``KeycloakGetError`` on the Admin API (typically 404 for an unknown user or a
    transient blip) resolves to ``[]`` so callers degrade to non-sysadmin rather than
    hard-failing the request. Guarantees that a Keycloak wobble cannot elevate
    privileges and cannot 500 a token-authenticated request."""
    admin = AsyncMock()
    admin.a_get_realm_roles_of_user = AsyncMock(side_effect=KeycloakGetError("keycloak unavailable"))
    patch_admin(admin)

    assert await KeycloakAdminService.get_user_realm_roles("user-1") == []


@pytest.mark.asyncio
async def test_non_keycloak_errors_still_propagate(patch_admin) -> None:
    """Only ``KeycloakGetError`` is swallowed — unexpected exceptions must still surface
    so they can be observed and triaged rather than silently reducing to ``[]``."""
    admin = AsyncMock()
    admin.a_get_realm_roles_of_user = AsyncMock(side_effect=RuntimeError("bug in client"))
    patch_admin(admin)

    with pytest.raises(RuntimeError, match="bug in client"):
        await KeycloakAdminService.get_user_realm_roles("user-1")
