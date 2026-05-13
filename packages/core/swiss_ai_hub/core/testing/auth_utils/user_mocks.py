from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import _create_admin
from swiss_ai_hub.core.auth.keycloak.models.keycloak_user import KeycloakUser
from swiss_ai_hub.core.infrastructure.api.startup_tenant_settings import StartupTenantSettings
from swiss_ai_hub.core.persistence.user.user_dashboard_entity import UserDashboardEntity
from swiss_ai_hub.core.testing.auth_utils.test_identity import (
    TEST_USER_EMAIL,
    TEST_USER_NAME,
    TEST_USER_OID,
    TEST_USER_ROLES,
)


def _create_mock_keycloak_user(user_id: str | None = None, email: str | None = None) -> KeycloakUser:
    return KeycloakUser(
        id=user_id or TEST_USER_OID,
        firstName=TEST_USER_NAME,
        lastName="",
        username=email or TEST_USER_EMAIL,
        email=email or TEST_USER_EMAIL,
        attributes={},
    )


#: Shared in-memory user store for the fake Keycloak admin. Tests can populate this
#: directly (e.g. via ``register_fake_keycloak_user``) to seed users that
#: ``KeycloakAdminService.get_user_by_id`` / ``find_user_by_email`` should return.
_FAKE_KEYCLOAK_USERS: dict[str, dict] = {}


def register_fake_keycloak_user(user_id: str, *, name: str, email: str, attributes: dict | None = None) -> None:
    """Registers a user in the fake Keycloak admin store.

    Call from test steps when you need ``KeycloakAdminService.get_user_by_id`` (or
    ``find_user_by_email``) to return a user with specific name/email for a given oid.
    """
    first, _, last = name.partition(" ")
    _FAKE_KEYCLOAK_USERS[user_id] = {
        "id": user_id,
        "username": email,
        "email": email,
        "firstName": first,
        "lastName": last,
        "attributes": attributes or {"active_tenant_id": [StartupTenantSettings().ID]},
    }


def _build_fake_admin() -> MagicMock:
    """Builds a stateful MagicMock standing in for a ``KeycloakAdmin`` instance.

    Keeps a per-user-id in-memory store so sequences like
    ``set_active_tenant`` → ``get_active_tenant_id`` return the value that was just
    written. Tests never hit a real Keycloak server.

    Seeds two users by default:
    - the fake test user (constants from ``test_identity``) that powers the
      bypassed auth flow used by most tests;
    - the superuser (``SuperuserSettings``) so ``initialize_superuser_token`` finds
      a Keycloak user by email during API lifespan startup.
    """
    from swiss_ai_hub.core.auth.superuser_settings import SuperuserSettings

    superuser = SuperuserSettings()

    def _default_user(user_id: str) -> dict:
        return {
            "id": user_id,
            "username": TEST_USER_EMAIL,
            "email": TEST_USER_EMAIL,
            "firstName": TEST_USER_NAME,
            "lastName": "",
            "attributes": {"active_tenant_id": [StartupTenantSettings().ID]},
        }

    users = _FAKE_KEYCLOAK_USERS
    users.setdefault(TEST_USER_OID, _default_user(TEST_USER_OID))
    users.setdefault(
        f"superuser-{superuser.USERNAME}",
        {
            "id": f"superuser-{superuser.USERNAME}",
            "username": superuser.USERNAME,
            "email": superuser.EMAIL,
            "firstName": "Super",
            "lastName": "User",
            "attributes": {"active_tenant_id": [StartupTenantSettings().ID]},
        },
    )

    async def a_get_user(user_id: str) -> dict:
        return users.setdefault(user_id, _default_user(user_id))

    async def a_get_users(query: dict | None = None) -> list[dict]:
        if query and "email" in query:
            return [u for u in users.values() if u.get("email") == query["email"]]
        return list(users.values())

    async def a_create_user(payload: dict, exist_ok: bool = True) -> str:
        user_id = payload.get("id") or TEST_USER_OID
        users.setdefault(user_id, _default_user(user_id))
        return user_id

    async def a_update_user(user_id: str, payload: dict) -> None:
        existing = users.setdefault(user_id, _default_user(user_id))
        existing.update(payload)
        if "attributes" in payload:
            existing["attributes"] = dict(payload["attributes"])

    async def a_get_user_groups(user_id: str) -> list[dict]:
        """Returns the user's Keycloak groups, derived from ``UserTenantRoleEntity`` rows.

        Tests assert "user X is a member of tenant Y" by creating a role entity row;
        since Keycloak is the real source of truth in production, the fake admin
        mirrors those rows back as ``/tenants/<id>`` group paths so membership checks
        that go through ``KeycloakAdminService.get_user_tenant_ids`` / ``is_user_member_of_tenant``
        succeed exactly when a role row exists for the pair.
        """
        from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity

        tenant_ids = UserTenantRoleEntity.get_tenant_ids_for_user(user_id)
        return [{"id": f"group-{tid}", "name": tid, "path": f"/tenants/{tid}"} for tid in tenant_ids]

    fake = MagicMock()
    fake.a_get_user = AsyncMock(side_effect=a_get_user)
    fake.a_get_users = AsyncMock(side_effect=a_get_users)
    fake.a_create_user = AsyncMock(side_effect=a_create_user)
    fake.a_update_user = AsyncMock(side_effect=a_update_user)
    fake.a_get_user_groups = AsyncMock(side_effect=a_get_user_groups)
    fake.a_get_group_by_path = AsyncMock(return_value={"id": "fake-group-id", "name": "tenants"})
    fake.a_get_group_members = AsyncMock(side_effect=lambda *_args, **_kwargs: list(users.values()))
    fake.a_create_group = AsyncMock(return_value="fake-group-id")
    fake.a_delete_group = AsyncMock(return_value=None)
    fake.a_group_user_add = AsyncMock(return_value=None)
    fake.a_group_user_remove = AsyncMock(return_value=None)
    fake.a_get_realm_roles_of_user = AsyncMock(return_value=[])
    fake.a_get_realm_role_members = AsyncMock(return_value=[])
    return fake


@pytest.fixture
def mock_keycloak_admin_service():
    """Patches ``_create_admin`` so every KeycloakAdminService method gets a fake client.

    One patch at the factory level is more robust than patching each staticmethod
    individually — it also survives ``@trace_fn``/``@staticmethod`` descriptor quirks
    and lru_cache interaction. Individual tests can still override specific methods
    via nested ``patch.object(KeycloakAdminService, ...)``.
    """
    _create_admin.cache_clear()
    _FAKE_KEYCLOAK_USERS.clear()
    fake_admin = _build_fake_admin()
    with patch(
        "swiss_ai_hub.core.auth.keycloak.keycloak_admin_service._create_admin",
        return_value=fake_admin,
    ):
        yield
    _FAKE_KEYCLOAK_USERS.clear()
    _create_admin.cache_clear()


def get_expected_user_data(include_dashboard=True, include_access=True):
    """
    Helper function to get expected user data for tests.
    Returns the user data that should be returned by API endpoints.
    """
    data = {
        "id": TEST_USER_OID,
        "name": TEST_USER_NAME,
        "email": TEST_USER_EMAIL,
        "profile_image": None,
        "roles": list(TEST_USER_ROLES),
        "is_sys_admin": False,
        "preferred_locale": None,
    }

    if include_dashboard:
        dashboard = UserDashboardEntity.create_default_dashboard()
        dashboard_dict = {
            "minRow": dashboard.minRow,
            "margin": dashboard.margin,
            "column": dashboard.column,
            "cellHeight": dashboard.cellHeight,
            "children": [
                {
                    "component": child.component,
                    "event": child.event,
                    "noResize": child.noResize,
                    "timeRange": child.timeRange,
                    "w": child.w,
                    "x": child.x,
                    "y": child.y,
                }
                for child in dashboard.children
            ],
        }
        data["dashboard"] = dashboard_dict

    if include_access:
        data["access"] = {
            "agents": [],
            "processes": [],
            "services": [{"level": 2, "name": "Mein Konto"}],
        }

    return data
