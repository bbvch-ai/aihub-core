import base64
import uuid

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from llama_index.core.base.llms.types import ChatMessage
from swiss_ai_hub.core.events.agent import UserMessageEvent
from swiss_ai_hub.core.infrastructure import create_s3_client, enable_logging
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler

from swiss_ai_hub.api.routes.agent.agent_controller import AgentController
from swiss_ai_hub.api.runners.simulation.agent.simulated_agent_api_test_runner import SimulatedAgentApiTestRunner

AGENT_CLASS = "TestAgent"
AGENT_ID = "test_agent_1"

enable_logging()


@pytest_asyncio.fixture
async def agent_api_client():
    auth = TestAuthHandler()
    controller = AgentController(auth=auth).get_all_agent_instances().get_agent_instance()
    runner = SimulatedAgentApiTestRunner(agent_class=AGENT_CLASS, agent_id=AGENT_ID).with_simple_chunk_events()
    runner.mount(controller)
    await runner.start_simulation()
    app = runner.create_app()

    async with LifespanManager(app) as lifespan:
        runner.create_agent_config_in_db()

        async with AsyncClient(
            transport=ASGITransport(app=lifespan.app), base_url="http://test/api/v1/active"
        ) as client:
            yield client

    await runner.stop_simulation()


@pytest.mark.asyncio
async def test_get_agent_instance(agent_api_client):
    """Test GET /agents/classes/{agent_class}/instances/{agent_id} returns correct agent details."""
    response = await agent_api_client.get(f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}")
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert data.get("agent_class") == AGENT_CLASS
    assert data.get("agent_id") == AGENT_ID
    for key in ("agent_config", "start_events", "stop_events"):
        assert key in data


@pytest.mark.asyncio
async def test_get_all_agent_instances(agent_api_client):
    """Test GET /agents/instances returns a list containing the simulated agent."""
    response = await agent_api_client.get("/agents/instances")
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert isinstance(data, list), "Response data should be a list"
    found = any(agent.get("agent_class") == AGENT_CLASS and agent.get("agent_id") == AGENT_ID for agent in data)
    assert found, "Simulated agent not found in agent instances"


@pytest.mark.asyncio
async def test_get_all_agent_instances_online_filter(agent_api_client):
    """Test GET /agents/instances?online=true returns online instances only."""
    response = await agent_api_client.get("/agents/instances?online=true")
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    assert isinstance(data, list), "Response data should be a list"
    # All returned instances should be online
    for agent in data:
        assert agent.get("is_online") is True, f"Expected online agent, got: {agent}"


@pytest.mark.asyncio
async def test_send_event_to_agent(agent_api_client):
    """Test POST /agents/classes/{agent_class}/instances/{agent_id}/{event_name} returns a stop event.

    Note: The response model is based on StopEvent (not LLMStopEvent) because LLMStopEvent's
    complex Message type with ContentBlock unions causes schema parsing issues with Jambo.
    """
    user_message = UserMessageEvent.api_input_model()(
        agent_id=AGENT_ID, messages=[ChatMessage(role="user", content="Hey!")]
    )
    path = f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}/{UserMessageEvent.event_name_from_class()}"
    response = await agent_api_client.post(
        url=path,
        content=user_message.model_dump_json(),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200, f"Response: {response.text}"

    data = response.json()
    # Response should contain display fields from StopEvent
    assert data.get("display_name"), f"Expected display_name, got: {data}"
    assert data.get("display_description"), f"Expected display_description, got: {data}"


@pytest_asyncio.fixture
async def simulated_agent():
    auth = TestAuthHandler()
    runner = SimulatedAgentApiTestRunner(agent_class=AGENT_CLASS, agent_id=AGENT_ID).with_simple_chunk_events()
    runner.mount(AgentController(auth=auth).get_image())
    await runner.start_simulation()
    app = runner.create_app()

    async with LifespanManager(app) as lifespan:
        runner.create_agent_config_in_db()
        async with AsyncClient(
            transport=ASGITransport(app=lifespan.app), base_url="http://test/api/v1/active"
        ) as client:
            yield client, runner

    await runner.stop_simulation()


@pytest.mark.asyncio
async def test_send_event_with_an_inline_file(simulated_agent):
    """The file is stored before publishing, so the agent receives only its reference, next to an uploaded one."""
    client, runner = simulated_agent
    uploaded = {"filename": "old.txt", "file_type": "text/plain", "file_id": str(uuid.uuid4())}
    inline = {"filename": "invoice.txt", "file_type": "text/plain", "content": base64.b64encode(b"Total: 42").decode()}

    response = await client.post(
        f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}/{UserMessageEvent.event_name_from_class()}",
        json={
            "messages": [{"role": "user", "blocks": [{"block_type": "text", "text": "Total?"}]}],
            "files": [inline, uploaded],
        },
    )

    assert response.status_code == 200, response.text
    received = next(event for event in runner.received_events if event.is_user_message_event)
    assert [file.filename for file in received.files] == ["invoice.txt", "old.txt"]
    assert "content" not in received.model_dump_json()
    bucket, key = received.files[0].resolve_s3_location(AGENT_CLASS, AGENT_ID)
    assert create_s3_client().get_object(Bucket=bucket, Key=key)["Body"].read() == b"Total: 42"


@pytest.mark.asyncio
async def test_a_rejected_inline_file_publishes_nothing(simulated_agent):
    client, runner = simulated_agent
    inline = {"filename": "archive.zip", "file_type": "application/zip", "content": base64.b64encode(b"PK").decode()}

    response = await client.post(
        f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}/{UserMessageEvent.event_name_from_class()}",
        json={"messages": [], "files": [inline]},
    )

    assert response.status_code == 415, response.text
    assert not any(event.is_user_message_event for event in runner.received_events)


@pytest.mark.asyncio
async def test_openapi_documents_the_inline_file_form(simulated_agent):
    client, _ = simulated_agent
    response = await client.get("http://test/api/v1/openapi.json")
    assert response.status_code == 200, response.text[:300]
    schemas = response.json()["components"]["schemas"]
    assert "content" in schemas["InlineFile"]["properties"]
    files = str(schemas["UserMessageEventInput"]["properties"]["files"])
    assert "InlineFile" in files and "UserUploadedFile" in files


@pytest.mark.asyncio
async def test_an_image_in_a_message_reaches_the_agent_as_a_reference(simulated_agent):
    client, runner = simulated_agent
    png = base64.b64encode(b"\x89PNG not really").decode()
    message = {
        "role": "user",
        "blocks": [
            {"block_type": "text", "text": "What is this?"},
            {"block_type": "image", "url": f"data:image/png;base64,{png}"},
        ],
    }

    response = await client.post(
        f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}/{UserMessageEvent.event_name_from_class()}",
        json={"messages": [message]},
    )

    assert response.status_code == 200, response.text
    received = next(event for event in runner.received_events if event.is_user_message_event)
    reference = str(received.messages[0].blocks[1].url)
    assert reference.startswith(f"s3://agent-files/{AGENT_CLASS}/{AGENT_ID}/images/")
    assert png not in received.model_dump_json()

    name = reference.rsplit("/", 1)[-1]
    image = await client.get(f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}/images/{name}")
    assert image.status_code == 200
    assert image.content == b"\x89PNG not really"
    assert image.headers["content-type"] == "image/png"
    assert image.headers["x-content-type-options"] == "nosniff"
    assert "sandbox" in image.headers["content-security-policy"]


@pytest.mark.asyncio
async def test_a_missing_image_is_not_found(simulated_agent):
    client, _ = simulated_agent
    response = await client.get(f"/agents/classes/{AGENT_CLASS}/instances/{AGENT_ID}/images/{'0' * 64}.png")
    assert response.status_code == 404
