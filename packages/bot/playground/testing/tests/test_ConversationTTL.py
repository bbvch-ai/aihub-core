import asyncio
import json
from datetime import datetime
from pathlib import Path

import pytest
import pytest_asyncio
import requests
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from swiss_ai_hub.core.routes import HealthController
from swiss_ai_hub.core.testing import ASGIAdapter
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler

from swiss_ai_hub.bot.persistence.entities.conversation_entity import (
    Content,
    ConversationEntity,
    ConversationTracker,
    Message,
)
from swiss_ai_hub.bot.persistence.entities.path_entity import Credentials, PathEntity
from swiss_ai_hub.bot.routes.agent.agent_chat_controller import AgentChatController
from swiss_ai_hub.bot.runners.simulated_agent_bot_test_runner import SimulatedAgentBotTestRunner

# Constants
BASE_URL = "http://test/api/v1"
AGENT_CLASS = "my_agent_class"
AGENT_ID = "my_agent_id"
JSON_ENDPOINT = f"{BASE_URL}/agent/chat/completions/{AGENT_CLASS}/{AGENT_ID}/json"
SERVICE_ENDPOINT = f"{BASE_URL}/service"

# Very short TTL for testing (in days)
TTL_DAYS = 1 / 86400  # 1 second TTL in days


@pytest.fixture
def patch_requests_adapter(monkeypatch, test_runner):
    """Patch the request.Session to forward all calls to our test application"""
    app = test_runner.create_app()
    original_session = requests.Session

    def session_factory(*args, **kwargs):
        session = original_session(*args, **kwargs)
        session.mount(BASE_URL, ASGIAdapter(app))
        return session

    monkeypatch.setattr(requests, "Session", session_factory)
    yield


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def test_runner():
    """Create a test runner with a very short TTL"""
    runner = SimulatedAgentBotTestRunner(agent_class=AGENT_CLASS, agent_id=AGENT_ID, conversation_ttl_days=TTL_DAYS)
    runner.with_simple_chunk_events()
    auth = TestAuthHandler()
    runner.mount(HealthController(auth=auth).get_health(), AgentChatController(auth=auth).completions_json())
    await runner.start_simulation()
    return runner


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def client(test_runner: SimulatedAgentBotTestRunner):
    """Create an HTTP client for testing"""
    app = test_runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def setup_test_credentials(client: AsyncClient):
    """Stores the endpoint's PathEntity through the Beanie client the bot's lifespan started."""
    json_path = f"/api/v1/agent/chat/completions/{AGENT_CLASS}/{AGENT_ID}/json"
    await PathEntity.find({"path": json_path}).delete()
    test_credentials = Credentials(
        APP_TYPE="MultiTenant", APP_ID="test_app_id", APP_PASSWORD="test_app_password", APP_TENANTID="test_tenant_id"
    )
    await PathEntity(path=json_path, credentials=test_credentials, system_message="Test system message").insert()

    yield

    await PathEntity.find({"path": json_path}).delete()


@pytest.mark.beanie
async def test_ttl_index_setup():
    """Test that the TTL index is correctly set up with the right TTL value"""
    # Update the TTL index with our test value
    await ConversationEntity.update_ttl_index(TTL_DAYS)

    # Get index information
    indexes = await ConversationEntity.get_pymongo_collection().index_information()

    # Look for the TTL index on last_activity
    ttl_index_found = False
    for index_name, index_info in indexes.items():
        if "last_activity" in [key for key, direction in index_info["key"]]:
            ttl_index_found = True
            assert "expireAfterSeconds" in index_info, "TTL index missing expireAfterSeconds"
            # Convert our TTL_DAYS to seconds for comparison
            expected_ttl_seconds = int(TTL_DAYS * 24 * 60 * 60)
            assert index_info["expireAfterSeconds"] == expected_ttl_seconds, (
                "TTL index has wrong expireAfterSeconds value"
            )

    assert ttl_index_found, "TTL index not found on last_activity field"


@pytest.mark.beanie
async def test_conversation_tracker_expired_detection():
    """Test that ConversationTracker correctly identifies expired conversations"""
    conversation_id = "test_expired_conversation"

    # 1. Create a conversation entity
    messages = [
        Message(user_id="test_user", content=[Content(text="Test", type="text")], role="user", name="Test User")
    ]
    bot_id = "test_bot_id"
    conversation = await ConversationEntity.create_conversation(conversation_id, bot_id, messages)

    # 2. Create a tracker entry
    await ConversationTracker.track_conversation(conversation_id, bot_id)

    # 3. Delete the conversation entity (simulating TTL expiration)
    await conversation.delete()

    # 4. Verify should_show_expiration_message returns True (conversation expired)
    should_show = await ConversationTracker.should_show_expiration_message(conversation_id, bot_id)
    assert should_show is True, "should_show_expiration_message should return True for expired conversation"

    # 5. Mark the conversation as explicitly deleted
    await ConversationTracker.mark_explicitly_deleted(conversation_id, bot_id)

    # 6. Verify should_show_expiration_message returns False (explicitly deleted)
    should_show = await ConversationTracker.should_show_expiration_message(conversation_id, bot_id)
    assert should_show is False, (
        "should_show_expiration_message should return False for explicitly deleted conversation"
    )


@pytest.mark.beanie
async def test_conversation_tracker_explicitly_deleted_vs_expired():
    """Test ConversationTracker distinguishes between explicitly deleted and expired conversations"""
    # Test IDs
    expired_id = "test_expired_conversation"
    deleted_id = "test_deleted_conversation"
    bot_id = "test_bot_id"

    # Create tracker entries for both
    expired_tracker = ConversationTracker(conversation_id=expired_id, bot_id=bot_id, explicitly_deleted=False)
    await expired_tracker.insert()

    deleted_tracker = ConversationTracker(conversation_id=deleted_id, bot_id=bot_id, explicitly_deleted=True)
    await deleted_tracker.insert()

    # No conversation entities exist for either ID (both are "absent")

    # Verify should_show_expiration_message results
    should_show_expired = await ConversationTracker.should_show_expiration_message(expired_id, bot_id)
    should_show_deleted = await ConversationTracker.should_show_expiration_message(deleted_id, bot_id)

    assert should_show_expired is True, "should_show_expiration_message should return True for expired conversation"
    assert should_show_deleted is False, (
        "should_show_expiration_message should return False for explicitly deleted conversation"
    )


@pytest.mark.asyncio(loop_scope="module")
async def test_conversation_ttl_with_bot(
    test_runner: SimulatedAgentBotTestRunner, client: AsyncClient, patch_requests_adapter, setup_test_credentials
):
    """Test creation of a conversation via the bot and verify TTL tracking"""
    # Load the user message template
    with open(Path(__file__).parent / "user_message.json") as file:
        payload: dict = json.loads(file.read())

    # Use a unique conversation ID
    conversation_id = f"ttl_test_{datetime.now().timestamp()}"
    bot_id = "test_bot_id"

    # Customize the message
    payload["serviceUrl"] = SERVICE_ENDPOINT
    payload["conversation"]["id"] = conversation_id
    payload["from"]["id"] = "test_user_id"
    payload["recipient"]["id"] = bot_id
    payload["id"] = "test_activity_id"
    payload["channelId"] = "emulator"  # Required by Bot Framework

    # Send a message via the bot to create a conversation
    response = await client.post(
        url=JSON_ENDPOINT,
        json=payload,
    )
    assert response.status_code == 200

    # Verify the conversation was created
    conversation = await ConversationEntity.get_conversation_by_conversation_id(conversation_id, bot_id)
    assert conversation is not None, "Conversation was not created in the database"

    # Verify the conversation tracker was created
    tracker = await ConversationTracker.get_tracker(conversation_id, bot_id)
    assert tracker is not None, "Conversation tracker was not created"
    assert tracker.explicitly_deleted is False

    for _ in range(10):
        await asyncio.sleep(10)
        # Check if the conversation still exists
        conversation = await ConversationEntity.get_conversation_by_conversation_id(conversation_id, bot_id)
        if conversation is None:
            break

    # Verify the expiration detection works correctly
    should_show = await ConversationTracker.should_show_expiration_message(conversation_id, bot_id)
    assert should_show is True, "should_show_expiration_message should return True for expired conversation"

    await ConversationTracker.delete_tracker(conversation_id, bot_id)
