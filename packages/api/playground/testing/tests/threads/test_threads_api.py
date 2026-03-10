from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from mongoengine import connect, disconnect
from swiss_ai_hub.core.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthHandler import (
    DangerousDevelopmentOnlyAuthHandler,
)
from swiss_ai_hub.core.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from swiss_ai_hub.core.infrastructure.api.AIHubSettings import AIHubSettings
from swiss_ai_hub.core.infrastructure.logging.logger import enable_logging
from swiss_ai_hub.core.infrastructure.mongo.MongoSettings import MongoSettings
from swiss_ai_hub.core.persistence.messaging.entities.ThreadEntity import ThreadEntity
from swiss_ai_hub.core.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: F401
from swiss_ai_hub.core.testing.auth_utils.tenant_mocks import mock_tenant_entity_autouse  # noqa: F401
from swiss_ai_hub.core.testing.auth_utils.user_mocks import mock_user_entity_autouse  # noqa: F401

from swiss_ai_hub.api.routes.thread.ThreadController import ThreadController
from swiss_ai_hub.api.runners.simulation.agent.SimulatedAgentApiTestRunner import SimulatedAgentApiTestRunner

enable_logging()

THREAD_BASE = "/api/v1/threads"
DEFAULT_USER_ID = DangerousDevelopmentOnlyAuthSettings().OID


@pytest.fixture(scope="module")
def mongodb():
    """Setup MongoDB connection and clear data after tests."""
    yield
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )
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


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def api_client(agent_class, agent_id, mongodb) -> AsyncGenerator[AsyncClient]:
    """Create an API client with ThreadController endpoints mounted."""
    runner = SimulatedAgentApiTestRunner(agent_class=agent_class, agent_id=agent_id)
    runner.with_simple_chunk_events()
    auth = DangerousDevelopmentOnlyAuthHandler()
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
    app = runner.create_app()
    async with LifespanManager(app) as lifespan:
        # Create agent config in database after DB connection is established
        runner.create_agent_config_in_db()
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
