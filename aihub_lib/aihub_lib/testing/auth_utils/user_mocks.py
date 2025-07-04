"""Mock fixtures for UserEntity methods used in testing."""

from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

import pytest

from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthConfig import (
    DangerousDevelopmentOnlyAuthConfig,
)
from aihub_lib.persistence.user.UserEntity import Dashboard, DashboardItem, UserEntity


def create_dashboard_with_items():
    """
    Create a dashboard with predefined items for testing.

    Returns a Dashboard object with three dashboard items: two DashboardComponentNumber
    and one DashboardComponentLineChart.
    """
    return Dashboard(
        minRow=1,
        margin=24,
        column=4,
        cellHeight=350,
        children=[
            DashboardItem(
                id=str(uuid4()),
                component="DashboardComponentNumber",
                noResize=True,
                timeRange="30d",
                event="StartEvent",
                x=0,
                y=0,
                w=1,
            ),
            DashboardItem(
                id=str(uuid4()),
                component="DashboardComponentLineChart",
                noResize=True,
                timeRange="30d",
                event="StartEvent",
                x=1,
                y=0,
                w=2,
            ),
            DashboardItem(
                id=str(uuid4()),
                component="DashboardComponentNumber",
                noResize=True,
                timeRange="30d",
                event="ExceptionEvent",
                x=3,
                y=0,
                w=1,
            ),
        ],
    )


def _create_mock_user_entity_function():
    """
    Create a mock function for UserEntity.by_oid that returns a dummy user.
    """
    config = DangerousDevelopmentOnlyAuthConfig()

    def mock_by_oid(user_oid):
        user = UserEntity(
            id=user_oid,
            name=config.NAME,
            email=config.EMAIL,
            roles=config.ROLES,
            profile_image=None,
            favorite_modules=[],
            dashboard=create_dashboard_with_items(),
            last_updated=datetime(2025, 7, 4, 12, 14, 45, 185140, tzinfo=timezone.utc),
        )
        return user

    return mock_by_oid


@pytest.fixture
def mock_user_entity():
    """
    Mock UserEntity.by_oid to return a dummy user with properties from DangerousDevelopmentOnlyAuthConfig.

    This fixture is useful for tests that need a consistent user object without database dependencies.

    This mock will return a user with the provided user_oid, regardless of what it is.
    This ensures that tests can use any user ID they want, not just the one from the config.
    """
    with patch.object(UserEntity, "by_oid", side_effect=_create_mock_user_entity_function()):
        yield


@pytest.fixture(autouse=True)
def mock_user_entity_autouse():
    """
    Auto-use version of the UserEntity mock for tests that always need it.
    This fixture is automatically applied to all tests in the module where it's imported.

    This mock will return a user with the provided user_oid, regardless of what it is.
    This ensures that tests can use any user ID they want, not just the one from the config.
    """
    with patch.object(UserEntity, "by_oid", side_effect=_create_mock_user_entity_function()):
        yield


def get_expected_user_data(include_dashboard=True, include_access=True):
    """
    Helper function to get expected user data for tests.
    Returns the user data that should be returned by API endpoints.

    Args:
        include_dashboard (bool): Whether to include dashboard data in the response
        include_access (bool): Whether to include access data in the response
    """
    config = DangerousDevelopmentOnlyAuthConfig()
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
        dashboard = create_dashboard_with_items()
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
            "services": [{"level": 2, "name": "User"}],
        }

    return data
