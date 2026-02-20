"""Mock fixtures for UserEntity methods used in testing."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.persistence.user.UserEntity import UserEntity


def _create_mock_user_entity_function():
    """
    Create a mock function for UserEntity.by_oid that returns a dummy user.
    """
    config = DangerousDevelopmentOnlyAuthSettings()

    def mock_by_oid(user_oid):
        user = UserEntity(
            id=user_oid,
            name=config.NAME,
            email=config.EMAIL,
            roles=config.ROLES,
            profile_image=None,
            favorite_modules=[],
            dashboard=UserEntity.create_default_dashboard(),
            last_updated=datetime(2025, 7, 4, 12, 14, 45, 185140, tzinfo=UTC),
        )
        return user

    return mock_by_oid


@pytest.fixture(autouse=True)
def mock_user_entity_autouse():
    """
    Mock UserEntity.by_oid to return a dummy user with properties from DangerousDevelopmentOnlyAuthSettings.

    This fixture is useful for tests that need a consistent user object without database dependencies.

    This mock will return a user with the provided user_oid, regardless of what it is.
    This ensures that tests can use any user ID they want, not just the one from the config.
    """
    with patch.object(UserEntity, "by_oid", side_effect=_create_mock_user_entity_function()):
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
            "services": [{"level": 2, "name": "My Account"}],
        }

    return data
