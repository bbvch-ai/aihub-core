import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from bson import ObjectId
from fastapi.testclient import TestClient
from typing import AsyncGenerator

from httpx import AsyncClient, ASGITransport
from mongoengine import connect, disconnect

from aihub_api.runners.SimulatedAgentApiTestRunner import SimulatedAgentApiTestRunner
from aihub_api.routes.thread.ThreadController import ThreadController
from aihub_lib.auth.dependencies.NoAuthHandler.NoAuthHandler import NoAuthHandler
from aihub_lib.infrastructure.ApiConfig import ApiConfig
from aihub_lib.infrastructure.azure.cosmos.CosmosAccess import CosmosAccess
from aihub_lib.persistence.messaging.entities.ThreadEntity import ThreadEntity
from aihub_lib.testing.logging.logger import enable_logging

enable_logging()

@pytest.fixture(scope="module")
def mongodb():
    """Setup a test MongoDB connection and clear data after each test."""
    yield
    connect(
        db=ApiConfig().DB_NAME,
        host=CosmosAccess().get_connection_string(),
        alias="default"
    )
    ThreadEntity.objects.delete()
    disconnect()

@pytest.fixture(scope="module")
def agent_class():
    return "test_agent"


@pytest.fixture(scope="module")
def agent_id():
    return "test_agent_1"


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def api_client(agent_class, agent_id, mongodb) -> AsyncGenerator[AsyncClient, None]:
    """Setup test client with simulated agent."""
    runner = SimulatedAgentApiTestRunner(agent_class=agent_class, agent_id=agent_id)
    runner.with_simple_chunk_events()

    auth = NoAuthHandler()
    runner.mount(
        ThreadController(auth=auth)
        .get_user_threads()
        .create_thread()
        .get_thread()
        .add_agent_to_thread()
        .remove_agent_from_thread()
        .add_user_to_thread()
        .remove_user_from_thread()
    )

    await runner.start_simulation()

    app = runner.get_app()

    async with LifespanManager(app) as lifespan:
        async with AsyncClient(
                transport=ASGITransport(app=lifespan.app), base_url="http://test"
        ) as client:
            yield client



@pytest.fixture
def thread_id():
    """Generate a valid MongoDB ObjectID as string."""
    return str(ObjectId())


@pytest.fixture
def create_thread_request(agent_class, agent_id):
    """Create a valid thread request."""
    return {
        "name": "Test Thread",
        "user_ids": ["1234567890"],  # Using the OID from NoAuthHandler
        "agents": [
            {
                "agent_id": agent_id,
                "agent_class": agent_class
            }
        ]
    }



@pytest.mark.asyncio(loop_scope="module")
async def test_create_thread(api_client, create_thread_request):
    """Test creating a new thread."""
    # When
    response = await api_client.post(f"/api/v1/thread/{thread_id}", json=create_thread_request)

    # Then
    assert response.status_code == 200, f"Response: {response.text}"
    data = response.json()
    assert data["name"] == create_thread_request["name"]
    assert len(data["users"]) >= 1  # Should at least include the authenticated user
    assert len(data["agents"]) == len(create_thread_request["agents"])

    # Verify the authenticated user is included
    user_ids = [user["id"] for user in data["users"]]
    assert "1234567890" in user_ids  # NoAuthHandler's default user ID

    # Verify the agent is included
    agent_ids = [agent["agent_id"] for agent in data["agents"]]
    assert create_thread_request["agents"][0]["agent_id"] in agent_ids


@pytest.mark.asyncio(loop_scope="module")
async def test_get_thread(api_client, thread_id, create_thread_request):
    """Test retrieving a specific thread."""
    # First create a thread
    await api_client.post(f"/api/v1/thread/{thread_id}", json=create_thread_request)

    # Then get it
    response = await api_client.get(f"/api/v1/thread/{thread_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == thread_id
    assert data["name"] == create_thread_request["name"]


@pytest.mark.asyncio(loop_scope="module")
async def test_get_user_threads(api_client, thread_id, create_thread_request):
    """Test listing all threads for a user."""
    # Create a thread first
    await api_client.post(f"/api/v1/thread/{thread_id}", json=create_thread_request)

    # Get all threads
    response = api_client.get("/api/v1/thread/")

    assert response.status_code == 200
    threads = response.json()
    assert len(threads) > 0
    assert any(thread["id"] == thread_id for thread in threads)


@pytest.mark.asyncio(loop_scope="module")
async def test_add_agent_to_thread(api_client, thread_id, create_thread_request, agent_class, agent_id):
    """Test adding an agent to an existing thread."""
    # Create thread first
    await api_client.post(f"/api/v1/thread/{thread_id}", json=create_thread_request)

    # Add new agent
    new_agent_request = {
        "agent_id": "new_agent_id",
        "agent_class": agent_class
    }
    response = await api_client.post(f"/api/v1/thread/{thread_id}/agents", json=new_agent_request)

    assert response.status_code == 200
    data = response.json()
    assert any(agent["agent_id"] == new_agent_request["agent_id"] for agent in data["agents"])


@pytest.mark.asyncio(loop_scope="module")
async def test_remove_agent_from_thread(api_client, thread_id, create_thread_request, agent_class, agent_id):
    """Test removing an agent from a thread."""
    # Create thread first
    await api_client.post(f"/api/v1/thread/{thread_id}", json=create_thread_request)

    # Remove agent
    response = await api_client.delete(f"/api/v1/thread/{thread_id}/agents/{agent_class}/{agent_id}")

    assert response.status_code == 200
    data = response.json()
    assert not any(agent["agent_id"] == agent_id for agent in data["agents"])


@pytest.mark.asyncio(loop_scope="module")
async def test_add_user_to_thread(api_client, thread_id, create_thread_request):
    """Test adding a user to an existing thread."""
    # Create thread first
    await api_client.post(f"/api/v1/thread/{thread_id}", json=create_thread_request)

    # Add new user
    new_user_request = {
        "user_id": "new_user_id"
    }
    response = await api_client.post(f"/api/v1/thread/{thread_id}/users", json=new_user_request)

    assert response.status_code == 200
    data = response.json()
    assert any(user["id"] == new_user_request["user_id"] for user in data["users"])


@pytest.mark.asyncio(loop_scope="module")
async def test_remove_user_from_thread(api_client, thread_id, create_thread_request):
    """Test removing a user from a thread."""
    # Create thread first
    await api_client.post(f"/api/v1/thread/{thread_id}", json=create_thread_request)

    # Remove user
    user_to_remove = create_thread_request["user_ids"][0]
    response = api_client.delete(f"/api/v1/thread/{thread_id}/users/{user_to_remove}")

    assert response.status_code == 200
    data = response.json()
    assert not any(user["id"] == user_to_remove for user in data["users"])


@pytest.mark.asyncio(loop_scope="module")
async def test_unauthorized_access(api_client, thread_id):
    """Test accessing a thread without proper authorization."""
    response = await api_client.get(f"/api/v1/thread/{thread_id}")
    assert response.status_code == 403