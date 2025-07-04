from unittest.mock import patch

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import AsyncClient, ASGITransport
from mongoengine import connect, disconnect

from aihub_api.runners.ApiTestRunner import ApiTestRunner
from aihub_api.routes.user.UserController import UserController
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider.DangerousDevelopmentOnlyIdentityProvider import (
    DangerousDevelopmentOnlyIdentityProvider,
)
from aihub_lib.infrastructure.ApiConfig import ApiConfig
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess
from aihub_lib.persistence.access.entities.RoleEntity import RoleEntity
from aihub_lib.persistence.user.UserEntity import UserEntity, Dashboard, DashboardItem
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthConfig import (
    DangerousDevelopmentOnlyAuthConfig,
)
from datetime import datetime, timezone
from uuid import uuid4

BASE_URL = "http://test"
USER_ENDPOINT = "/api/v1/users/me"
EXPECTED_USER_FIELDS = ["id", "name", "email"]


@pytest.fixture(scope="module", autouse=True)
def mongo_db():
    """Set up and tear down the MongoDB connection for tests."""
    connect(db=ApiConfig().DB_NAME, host=CosmosAccess().get_connection_string())
    yield
    disconnect()


@pytest_asyncio.fixture(scope="module")
async def api_client():
    """Create a test client for the API with UserController mounted."""
    runner = ApiTestRunner()
    auth = DangerousDevelopmentOnlyAuthHandler(identity_provider=DangerousDevelopmentOnlyIdentityProvider())
    runner.mount(UserController(auth=auth).get_my_user())
    app = runner.get_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest.fixture(autouse=True)
def mock_role_entity_methods():
    """
    Mock RoleEntity methods to ensure the 'TestOnlyFullAdminAccess' role is recognized during tests.
    """
    original_filter_existing_roles = RoleEntity.filter_existing_roles
    original_get_access_rules_for_roles = RoleEntity.get_access_rules_for_roles

    def mock_filter_existing_roles(role_names):
        filtered_roles = original_filter_existing_roles(role_names)
        if "TestOnlyFullAdminAccess" in role_names and "TestOnlyFullAdminAccess" not in filtered_roles:
            filtered_roles.append("TestOnlyFullAdminAccess")
        return filtered_roles

    def mock_get_access_rules_for_roles(role_names):
        access_rules = original_get_access_rules_for_roles(role_names)
        if "TestOnlyFullAdminAccess" in role_names:
            access_rules.add("aihub.admin.>")
        return access_rules

    with patch.object(RoleEntity, "filter_existing_roles", side_effect=mock_filter_existing_roles):
        with patch.object(RoleEntity, "get_access_rules_for_roles", side_effect=mock_get_access_rules_for_roles):
            yield


@pytest.fixture(autouse=True)
def mock_user_entity():
    """Mock UserEntity.by_oid to return a dummy user with properties from DangerousDevelopmentOnlyAuthConfig."""
    config = DangerousDevelopmentOnlyAuthConfig()

    def create_dashboard():
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

    def mock_by_oid(user_oid):
        # Create a dummy user with properties from DangerousDevelopmentOnlyAuthConfig
        # Use the provided user_oid instead of config.OID
        user = UserEntity(
            id=user_oid,
            name=config.NAME,
            email=config.EMAIL,
            roles=config.ROLES,
            profile_image=None,
            favorite_modules=[],
            dashboard=create_dashboard(),
            last_updated=datetime(2025, 7, 4, 12, 14, 45, 185140, tzinfo=timezone.utc),
        )
        return user

    with patch.object(UserEntity, "by_oid", side_effect=mock_by_oid):
        yield


@pytest.fixture
def expected_user_data():
    """Expected user data from DangerousDevelopmentOnlyAuthConfig."""
    config = DangerousDevelopmentOnlyAuthConfig()
    return {
        "id": config.OID,
        "name": config.NAME,
        "email": config.EMAIL,
        "profile_image": None,
        "favorite_modules": [],
        "roles": config.ROLES,
        "access": {
            "agents": [],
            "processes": [],
            "services": [{"level": 2, "name": "User"}],
        },
        "last_accessed": "2025-07-04T12:14:45.185140Z",
        "dashboard": {
            "cellHeight": 350,
            "children": [
                {
                    "component": "DashboardComponentNumber",
                    "event": "StartEvent",
                    "noResize": True,
                    "timeRange": "30d",
                    "w": 1,
                    "x": 0,
                    "y": 0,
                },
                {
                    "component": "DashboardComponentLineChart",
                    "event": "StartEvent",
                    "noResize": True,
                    "timeRange": "30d",
                    "w": 2,
                    "x": 1,
                    "y": 0,
                },
                {
                    "component": "DashboardComponentNumber",
                    "event": "ExceptionEvent",
                    "noResize": True,
                    "timeRange": "30d",
                    "w": 1,
                    "x": 3,
                    "y": 0,
                },
            ],
            "column": 4,
            "margin": 24,
            "minRow": 1,
        },
    }


@pytest.mark.asyncio
async def test_get_user_endpoint(api_client, expected_user_data):
    """Test GET /user/me returns expected user data."""
    headers = {"Content-Type": "application/json"}
    response = await api_client.get(USER_ENDPOINT, headers=headers)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    user_data = response.json()
    user_data["access"]["agents"] = []
    user_data["access"]["processes"] = []
    for child in user_data["dashboard"]["children"]:
        del child["id"]
    assert isinstance(user_data, dict)
    assert all(key in user_data for key in EXPECTED_USER_FIELDS)
    assert user_data == expected_user_data


@pytest.mark.asyncio
async def test_user_dto_structure(api_client):
    """Test that user DTO has the expected structure."""
    response = await api_client.get(USER_ENDPOINT)
    user_data = response.json()
    assert isinstance(user_data["id"], str)
    assert isinstance(user_data["name"], str)
    assert isinstance(user_data["email"], str)
    assert "@" in user_data["email"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "headers",
    [
        {"Content-Type": "application/json"},
        {"Accept": "application/json"},
        {},
    ],
)
async def test_user_endpoint_different_headers(api_client, headers):
    """Test GET /user/me with various headers."""
    response = await api_client.get(USER_ENDPOINT, headers=headers)
    assert response.status_code == 200
    assert "id" in response.json()
