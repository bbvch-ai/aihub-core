from unittest.mock import patch

import pytest

from swiss_ai_hub.core.auth.dependencies.dangerous_development_only_auth_handler.dangerous_development_only_auth_settings import (  # noqa: E501
    DangerousDevelopmentOnlyAuthSettings,
)
from swiss_ai_hub.core.auth.keycloak.keycloak_admin_service import KeycloakAdminService
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


@pytest.fixture(autouse=True)
def mock_keycloak_admin_service_autouse():
    """
    Mock KeycloakAdminService methods to return dummy user data.

    Mocks get_user_by_id, find_user_by_email, get_users_by_ids, get_active_tenant_id,
    and set_active_tenant so tests don't need a real Keycloak instance.
    """

    async def mock_get_user_by_id(keycloak_user_id):
        return _create_mock_keycloak_user(user_id=keycloak_user_id)

    async def mock_find_user_by_email(email):
        return _create_mock_keycloak_user(email=email)

    async def mock_get_users_by_ids(keycloak_user_ids):
        return {uid: _create_mock_keycloak_user(user_id=uid) for uid in keycloak_user_ids}

    async def mock_get_active_tenant_id(user_id):
        return None

    async def mock_set_active_tenant(user_id, tenant_id):
        pass

    with (
        patch.object(KeycloakAdminService, "get_user_by_id", side_effect=mock_get_user_by_id),
        patch.object(KeycloakAdminService, "find_user_by_email", side_effect=mock_find_user_by_email),
        patch.object(KeycloakAdminService, "get_users_by_ids", side_effect=mock_get_users_by_ids),
        patch.object(KeycloakAdminService, "get_active_tenant_id", side_effect=mock_get_active_tenant_id),
        patch.object(KeycloakAdminService, "set_active_tenant", side_effect=mock_set_active_tenant),
    ):
        yield


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
