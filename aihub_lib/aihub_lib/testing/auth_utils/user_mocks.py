from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.persistence.user.UserEntity import UserEntity

MOCK_USER_LAST_UPDATED = datetime(2025, 7, 4, 12, 14, 45, 185140, tzinfo=UTC)


def _create_mock_user(user_id: str | None = None, email: str | None = None) -> UserEntity:
    """Create a mock UserEntity with properties from DangerousDevelopmentOnlyAuthSettings."""
    config = DangerousDevelopmentOnlyAuthSettings()
    return UserEntity(
        id=user_id or config.OID,
        name=config.NAME,
        email=email or config.EMAIL,
        profile_image=None,
        favorite_modules=[],
        dashboard=UserEntity.create_default_dashboard(),
        last_updated=MOCK_USER_LAST_UPDATED,
    )


@pytest.fixture(autouse=True)
def mock_user_entity_autouse():
    """
    Mock UserEntity lookup and creation methods to return a dummy user.

    Mocks by_oid, by_email, and ensure_user_exists so tests don't need a real database.
    The mock user has properties from DangerousDevelopmentOnlyAuthSettings.
    """

    def mock_by_oid(user_oid):
        return _create_mock_user(user_id=user_oid)

    def mock_by_email(email):
        return _create_mock_user(email=email)

    def mock_ensure_user_exists(oid, name, email, profile_image=None):
        return _create_mock_user(user_id=oid, email=email)

    def mock_get_by_ids(user_ids):
        return {uid: _create_mock_user(user_id=uid) for uid in user_ids}

    with (
        patch.object(UserEntity, "by_oid", side_effect=mock_by_oid),
        patch.object(UserEntity, "by_email", side_effect=mock_by_email),
        patch.object(UserEntity, "ensure_user_exists", side_effect=mock_ensure_user_exists),
        patch.object(UserEntity, "get_by_ids", side_effect=mock_get_by_ids),
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
        "favorite_modules": [],
        "last_accessed": "2025-07-04T12:14:45.185140Z",
    }

    if include_dashboard:
        # Create a version of the dashboard data without the random IDs
        dashboard = UserEntity.create_default_dashboard()
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
