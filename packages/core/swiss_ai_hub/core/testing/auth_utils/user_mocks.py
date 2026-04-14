from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from swiss_ai_hub.core.auth.dependencies.dangerous_development_only_auth_handler.dangerous_development_only_auth_settings import (  # noqa: E501
    DangerousDevelopmentOnlyAuthSettings,
)
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import _create_admin
from swiss_ai_hub.core.auth.keycloak.models.keycloak_user import KeycloakUser
from swiss_ai_hub.core.persistence.user.user_dashboard_entity import UserDashboardEntity


def _create_mock_keycloak_user(user_id: str | None = None, email: str | None = None) -> KeycloakUser:
    config = DangerousDevelopmentOnlyAuthSettings()
    return KeycloakUser(
        id=user_id or config.OID,
        firstName=config.NAME,
        lastName="",
        username=email or config.EMAIL,
        email=email or config.EMAIL,
        attributes={},
    )


def _build_fake_admin() -> MagicMock:
    """Builds a MagicMock standing in for a ``KeycloakAdmin`` instance.

    Returns sensible defaults for every method the ``KeycloakAdminService`` uses so that
    the real static methods can run end-to-end without hitting a real Keycloak server.
    """
    config = DangerousDevelopmentOnlyAuthSettings()
    user_dict = {
        "id": config.OID,
        "username": config.EMAIL,
        "email": config.EMAIL,
        "firstName": config.NAME,
        "lastName": "",
        "attributes": {},
    }

    fake = MagicMock()
    fake.a_get_user = AsyncMock(return_value=user_dict)
    fake.a_get_users = AsyncMock(return_value=[user_dict])
    fake.a_create_user = AsyncMock(return_value=config.OID)
    fake.a_update_user = AsyncMock(return_value=None)
    fake.a_get_group_by_path = AsyncMock(return_value={"id": "fake-group-id", "name": "tenants"})
    fake.a_get_group_members = AsyncMock(return_value=[user_dict])
    fake.a_create_group = AsyncMock(return_value="fake-group-id")
    fake.a_delete_group = AsyncMock(return_value=None)
    fake.a_group_user_add = AsyncMock(return_value=None)
    fake.a_group_user_remove = AsyncMock(return_value=None)
    return fake


@pytest.fixture(autouse=True, scope="session")
def mock_keycloak_admin_service_autouse():
    """Patches ``_create_admin`` so every KeycloakAdminService method gets a fake client.

    One patch at the factory level is more robust than patching each staticmethod
    individually — it also survives ``@trace_fn``/``@staticmethod`` descriptor quirks
    and lru_cache interaction. Individual tests can still override specific methods
    via nested ``patch.object(KeycloakAdminService, ...)``.
    """
    _create_admin.cache_clear()
    fake_admin = _build_fake_admin()
    with patch(
        "swiss_ai_hub.core.auth.keycloak.keycloak_admin_service._create_admin",
        return_value=fake_admin,
    ):
        yield
    _create_admin.cache_clear()


def get_expected_user_data(include_dashboard=True, include_access=True):
    """
    Helper function to get expected user data for tests.
    Returns the user data that should be returned by API endpoints.
    """
    config = DangerousDevelopmentOnlyAuthSettings()
    data = {
        "id": config.OID,
        "name": config.NAME,
        "email": config.EMAIL,
        "profile_image": None,
        "roles": config.ROLES,
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
