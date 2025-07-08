from datetime import datetime, timezone
from unittest.mock import patch

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from typing import AsyncGenerator

from httpx import AsyncClient, ASGITransport
from mongoengine import connect, disconnect

from aihub_api.runners.SimulatedAgentApiTestRunner import SimulatedAgentApiTestRunner
from aihub_api.routes.thread.ThreadController import ThreadController
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthConfig import (
    DangerousDevelopmentOnlyAuthConfig,
)
from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider.DangerousDevelopmentOnlyIdentityProvider import (
    DangerousDevelopmentOnlyIdentityProvider,
)
from aihub_lib.infrastructure.ApiConfig import ApiConfig
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess
from aihub_lib.persistence.messaging.entities.ThreadEntity import ThreadEntity
from aihub_lib.persistence.user.UserEntity import UserEntity, Dashboard
from aihub_lib.testing.logging.logger import enable_logging
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_admin_only  # noqa: F401

enable_logging()

THREAD_BASE = "/api/v1/threads"
DEFAULT_USER_ID = DangerousDevelopmentOnlyAuthConfig().OID


@pytest.fixture(scope="module")
def mongodb():
    """Setup MongoDB connection and clear data after tests."""
    yield
    connect(db=ApiConfig().DB_NAME, host=CosmosAccess().get_connection_string())
    ThreadEntity.objects.delete()
    disconnect()


@pytest.fixture(scope="module")
def agent_class() -> str:
    """Return test agent class."""
    return "test_agent"


@pytest.fixture(scope="module")
def agent_id() -> str:
    """Return test agent ID."""
    return "test_agent_1"



@pytest.fixture(autouse=True)
def mock_user_entity():
    """Mock UserEntity.by_oid to return a dummy user with properties from DangerousDevelopmentOnlyAuthConfig."""
    config = DangerousDevelopmentOnlyAuthConfig()

    def mock_by_oid(user_oid):
        user = UserEntity(
            id=user_oid,
            name=config.NAME,
            email=config.EMAIL,
            roles=config.ROLES,
            profile_image=None,
            favorite_modules=[],
            dashboard=Dashboard(minRow=1, margin=24, column=4, cellHeight=350, children=[]),
            last_updated=datetime(2025, 7, 4, 12, 14, 45, 185140, tzinfo=timezone.utc),
        )
        return user

    with patch.object(UserEntity, "by_oid", side_effect=mock_by_oid):
        yield


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def api_client(agent_class, agent_id, mongodb) -> AsyncGenerator[AsyncClient, None]:
    """Create an API client with ThreadController endpoints mounted."""
    runner = SimulatedAgentApiTestRunner(agent_class=agent_class, agent_id=agent_id)
    runner.with_simple_chunk_events()
    auth = DangerousDevelopmentOnlyAuthHandler(identity_provider=DangerousDevelopmentOnlyIdentityProvider())
    controller = (
        ThreadController(auth=auth)
        .get_user_threads()
        .create_thread()
        .get_thread()
        .add_agent_to_thread()
        .remove_agent_from_thread()
        .add_user_to_thread()
        .remove_user_from_thread()
    )
    runner.mount(controller)
    await runner.start_simulation()
    app = runner.get_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url="http://test") as client:
            yield client


@pytest.fixture
def create_thread_request(agent_class, agent_id):
    """Return a valid thread creation request with one user and one agent."""
    return {
        "name": "Test Thread",
        "user_ids": [DEFAULT_USER_ID],
        "agents": [{"agent_id": agent_id, "agent_class": agent_class}],
    }


@pytest.fixture
def create_empty_thread_request(agent_class, agent_id):
    """Return a valid thread creation request with no users or agents."""
    return {"name": "Test Thread", "user_ids": [], "agents": []}


@pytest.mark.asyncio(loop_scope="module")
async def test_create_thread(api_client, create_thread_request):
    """Test creating a new thread returns valid thread details."""
    response = await api_client.post(f"{THREAD_BASE}/", json=create_thread_request)
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data["name"] == create_thread_request["name"]
    assert len(data["users"]) >= 1
    assert len(data["agents"]) == len(create_thread_request["agents"])
    user_ids = [user["id"] for user in data["users"]]
    assert DEFAULT_USER_ID in user_ids
    agent_ids = [agent["agent_id"] for agent in data["agents"]]
    assert create_thread_request["agents"][0]["agent_id"] in agent_ids


@pytest.mark.asyncio(loop_scope="module")
async def test_get_thread(api_client, create_thread_request):
    """Test retrieving a specific thread returns correct details."""
    create_response = await api_client.post(f"{THREAD_BASE}/", json=create_thread_request)
    thread_id = create_response.json()["id"]
    response = await api_client.get(f"{THREAD_BASE}/{thread_id}")
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data["id"] == thread_id
    assert data["name"] == create_thread_request["name"]


@pytest.mark.asyncio(loop_scope="module")
async def test_get_user_threads(api_client, create_thread_request):
    """Test listing all threads for a user returns the created thread."""
    create_response = await api_client.post(f"{THREAD_BASE}/", json=create_thread_request)
    thread_id = create_response.json()["id"]
    response = await api_client.get(f"{THREAD_BASE}/")
    assert response.status_code == 200, f"Response: {response.text}"
    paged_response = response.json()
    threads = paged_response["threads"]
    assert len(threads) > 0
    assert any(thread["id"] == thread_id for thread in threads)


@pytest.mark.asyncio(loop_scope="module")
async def test_add_agent_to_thread(api_client, create_empty_thread_request, agent_class, agent_id):
    """Test adding an agent to an existing thread returns updated agent list."""
    create_response = await api_client.post(f"{THREAD_BASE}/", json=create_empty_thread_request)
    thread_id = create_response.json()["id"]
    new_agent_request = {"agent_id": agent_id, "agent_class": agent_class}
    response = await api_client.post(f"{THREAD_BASE}/{thread_id}/agents", json=new_agent_request)
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert any(agent["agent_id"] == new_agent_request["agent_id"] for agent in data["agents"])


@pytest.mark.asyncio(loop_scope="module")
async def test_remove_agent_from_thread(api_client, create_thread_request, agent_class, agent_id):
    """Test removing an agent from a thread returns updated agent list."""
    create_response = await api_client.post(f"{THREAD_BASE}/", json=create_thread_request)
    thread_id = create_response.json()["id"]
    response = await api_client.delete(f"{THREAD_BASE}/{thread_id}/agents/{agent_class}/{agent_id}")
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert not any(agent["agent_id"] == agent_id for agent in data["agents"])


@pytest.mark.asyncio(loop_scope="module")
async def test_add_user_to_thread(api_client, create_empty_thread_request):
    """Test adding a user to a thread returns updated user list."""
    create_response = await api_client.post(f"{THREAD_BASE}/", json=create_empty_thread_request)
    thread_id = create_response.json()["id"]
    new_user_request = {"user_id": DEFAULT_USER_ID}
    response = await api_client.post(f"{THREAD_BASE}/{thread_id}/users", json=new_user_request)
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert any(user["id"] == new_user_request["user_id"] for user in data["users"])


@pytest.mark.asyncio(loop_scope="module")
async def test_remove_user_from_thread(api_client, create_thread_request):
    """Test removing a user from a thread returns updated user list."""
    create_response = await api_client.post(f"{THREAD_BASE}/", json=create_thread_request)
    thread_id = create_response.json()["id"]
    user_to_remove = create_thread_request["user_ids"][0]
    response = await api_client.delete(f"{THREAD_BASE}/{thread_id}/users/{user_to_remove}")
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert not any(user["id"] == user_to_remove for user in data["users"])
