import asyncio
import json
from pathlib import Path

import pytest
import pytest_asyncio
import requests
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from mongoengine import connect, disconnect
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings, enable_logging
from swiss_ai_hub.core.infrastructure.api.startup_tenant_settings import StartupTenantSettings
from swiss_ai_hub.core.persistence.access.entities.tenant_metadata_entity import TenantMetadataEntity
from swiss_ai_hub.core.persistence.access.entities.user_tenant_role_entity import UserTenantRoleEntity
from swiss_ai_hub.core.persistence.messaging.entities.thread_entity import ThreadEntity
from swiss_ai_hub.core.persistence.utils import str_to_object_id
from swiss_ai_hub.core.routes import HealthController
from swiss_ai_hub.core.testing import ASGIAdapter
from swiss_ai_hub.core.testing.auth_utils import TEST_USER_OID, TestAuthHandler
from swiss_ai_hub.core.testing.auth_utils.user_mocks import register_fake_keycloak_user

from swiss_ai_hub.bot.persistence.entities.conversation_entity import ConversationEntity
from swiss_ai_hub.bot.persistence.entities.path_entity import Credentials, PathEntity
from swiss_ai_hub.bot.routes.agent.agent_chat_controller import AgentChatController
from swiss_ai_hub.bot.runners.simulated_agent_bot_test_runner import SimulatedAgentBotTestRunner

pytestmark = pytest.mark.usefixtures("cleanup_conversation")

enable_logging()

BASE_URL = "http://test/api/v1"
PORT = 8001
AGENT_CLASS = "my_agent_class"
AGENT_ID = "my_agent_id"

JSON_ENDPOINT = f"{BASE_URL}/agent/chat/completions/{AGENT_CLASS}/{AGENT_ID}/json"
STREAM_ENDPOINT = f"{BASE_URL}/agent/chat/completions/{AGENT_CLASS}/{AGENT_ID}/stream"
SERVICE_ENDPOINT = f"{BASE_URL}/service"

CONVERSATION_ID = "test_conversation_id"
BOT_ID = "test_bot_id"
USER_ID = "test_user_id"
USER_EMAIL = "test@example.com"
ACTIVITY_ID = "test_activity_id"


@pytest.fixture(scope="module")
def setup_test_credentials():
    """Set up PathEntity credentials for test endpoints"""
    # Connect to MongoDB
    connect(
        db=AIHubSettings().MONGO_MAIN_DB_NAME,
        host=MongoSettings().CONNECTION_STRING.get_secret_value(),
        uuidRepresentation="standard",
    )

    # Create credentials for JSON endpoint
    json_path = f"/api/v1/agent/chat/completions/{AGENT_CLASS}/{AGENT_ID}/json"
    stream_path = f"/api/v1/agent/chat/completions/{AGENT_CLASS}/{AGENT_ID}/stream"

    # Clean up any existing test credentials
    PathEntity.objects(path=json_path).delete()
    PathEntity.objects(path=stream_path).delete()

    # Create test credentials
    test_credentials = Credentials(
        APP_TYPE="MultiTenant", APP_ID="test_app_id", APP_PASSWORD="test_app_password", APP_TENANTID="test_tenant_id"
    )

    # Create PathEntity records for both endpoints
    PathEntity(path=json_path, credentials=test_credentials, system_message="Test system message").save()
    PathEntity(path=stream_path, credentials=test_credentials, system_message="Test system message").save()

    # Create default tenant and assign test user
    default_tenant = TenantMetadataEntity.ensure_startup_tenant_metadata_exists(
        tenant_id=StartupTenantSettings().ID, name=StartupTenantSettings().NAME, access_rules=["aihub.admin.>"]
    )
    tenant_id = str(default_tenant.id)

    # Assign test user to default tenant with admin role. Use the OID that
    # ``KeycloakAdminService.find_user_by_email`` resolves to in tests (the fake
    # admin returns a single stub user keyed by this OID).
    dev_oid = TEST_USER_OID
    UserTenantRoleEntity.create_or_update(
        user_id=dev_oid,
        tenant_id=tenant_id,
        roles=["admin"],
        validate_roles=False,
    )

    # Seed the fake Keycloak admin store so ``find_user_by_email(USER_EMAIL)``
    # resolves to the dev OID. The bot sends ``from_property.name = USER_EMAIL``
    # which is looked up via email.
    register_fake_keycloak_user(user_id=dev_oid, name="Test User", email=USER_EMAIL)

    yield

    # Clean up test data
    try:
        PathEntity.objects(path=json_path).delete()
        PathEntity.objects(path=stream_path).delete()
        UserTenantRoleEntity.objects(user_id=dev_oid).delete()
    except Exception:
        # Connection may already be closed, ignore cleanup errors
        pass
    finally:
        try:
            disconnect()
        except Exception:
            pass


@pytest.fixture
def patch_requests_adapter(monkeypatch, test_runner):
    """Patch the request.Session to forward all calls made to the test domain to our fastapi application"""
    app = test_runner.create_app()
    original_session = requests.Session

    def session_factory(*args, **kwargs):
        session = original_session(*args, **kwargs)
        session.mount(BASE_URL, ASGIAdapter(app))
        return session

    monkeypatch.setattr(requests, "Session", session_factory)
    yield


@pytest.fixture
def cleanup_conversation():
    """Clean up conversation and thread state before each test."""
    thread_id = str(str_to_object_id(CONVERSATION_ID))
    # Clean up before test (connection may not exist yet)
    try:
        ConversationEntity.objects(conversation_id=CONVERSATION_ID).delete()
        ThreadEntity.objects(id=thread_id).delete()
    except Exception:
        pass
    yield
    # Clean up after test (connection may be closed)
    try:
        ConversationEntity.objects(conversation_id=CONVERSATION_ID).delete()
        ThreadEntity.objects(id=thread_id).delete()
    except Exception:
        pass


@pytest_asyncio.fixture(scope="function")
async def test_runner(captured_responses):
    runner = SimulatedAgentBotTestRunner(agent_class=AGENT_CLASS, agent_id=AGENT_ID)
    runner.with_simple_chunk_events()
    runner.responses = captured_responses  # Wire captured responses to test_runner
    auth = TestAuthHandler()
    runner.mount(
        HealthController(auth=auth).get_health(), AgentChatController(auth=auth).completions_json().completions_stream()
    )
    await runner.start_simulation()
    return runner


@pytest_asyncio.fixture(scope="function")
async def client(test_runner: SimulatedAgentBotTestRunner):
    app = test_runner.create_app()
    async with LifespanManager(app) as lifespan:
        async with AsyncClient(transport=ASGITransport(app=lifespan.app), base_url=BASE_URL) as client:
            yield client


@pytest.mark.asyncio
async def test_send_message(
    test_runner: SimulatedAgentBotTestRunner, client: AsyncClient, patch_requests_adapter, setup_test_credentials
):
    with open(Path(__file__).parent / "user_message.json") as file:
        payload: dict = json.loads(file.read())

    payload["serviceUrl"] = SERVICE_ENDPOINT
    payload["conversation"]["id"] = CONVERSATION_ID
    payload["from"]["id"] = USER_ID
    payload["from"]["name"] = USER_EMAIL
    payload["recipient"]["id"] = BOT_ID
    payload["id"] = ACTIVITY_ID
    payload["channelId"] = "emulator"  # Required by Bot Framework

    response = await client.post(
        url=JSON_ENDPOINT,
        json=payload,
    )

    assert response.status_code == 200
    assert test_runner.responses[-1].path == f"/v3/conversations/{CONVERSATION_ID}/activities/{ACTIVITY_ID}"
    assert test_runner.responses[-1].payload["type"] == "message"
    assert test_runner.responses[-1].payload["conversation"]["id"] == CONVERSATION_ID
    assert test_runner.responses[-1].payload["from"]["id"] == BOT_ID
    assert test_runner.responses[-1].payload["recipient"]["id"] == USER_ID
    assert test_runner.responses[-1].payload["text"] == "First chunk.\nSecond chunk."


@pytest.mark.asyncio
async def test_unprovisioned_user_is_prompted_to_log_in(
    test_runner: SimulatedAgentBotTestRunner, client: AsyncClient, patch_requests_adapter, setup_test_credentials
):
    """Issue #1315: a Teams/bot-first user with no Keycloak account gets an actionable message.

    The user's email (``ghost@example.com``) is never registered in the fake Keycloak store, so
    ``resolve_user_identity`` raises ``UserNotProvisionedError``. Instead of the opaque generic
    error, the bot now replies with the ``user_not_provisioned`` message telling the user to sign in
    to the Hub web portal first — never reaching the agent.
    """
    with open(Path(__file__).parent / "user_message.json") as file:
        payload: dict = json.loads(file.read())

    payload["serviceUrl"] = SERVICE_ENDPOINT
    payload["conversation"]["id"] = CONVERSATION_ID
    payload["from"]["id"] = USER_ID
    payload["from"]["name"] = "ghost@example.com"  # an email NOT provisioned in Keycloak
    payload["recipient"]["id"] = BOT_ID
    payload["id"] = ACTIVITY_ID
    payload["channelId"] = "emulator"

    response = await client.post(url=JSON_ENDPOINT, json=payload)

    # The webhook itself succeeds; the failure is surfaced to the user as a chat reply.
    assert response.status_code == 200

    reply_text = test_runner.responses[-1].payload["text"]
    # The unprovisioned user never reaches the agent — no real answer.
    assert reply_text != "First chunk.\nSecond chunk."
    # They get the actionable "log in to the Hub first" message (with the portal URL), not the
    # opaque generic error.
    locale_handler = LocaleHandler().in_locale("en")
    login_url = AIHubSettings().primary_frontend_origin
    assert reply_text == locale_handler("bot.error.user_not_provisioned", url=login_url)
    assert login_url in reply_text
    assert reply_text != locale_handler("bot.error.generic_error")


@pytest.mark.flaky
@pytest.mark.asyncio
async def test_stream_response(
    test_runner: SimulatedAgentBotTestRunner, client: AsyncClient, patch_requests_adapter, setup_test_credentials
):
    with open(Path(__file__).parent / "user_message.json") as file:
        payload: dict = json.loads(file.read())

    payload["serviceUrl"] = SERVICE_ENDPOINT
    payload["conversation"]["id"] = CONVERSATION_ID
    payload["from"]["id"] = USER_ID
    payload["from"]["name"] = USER_EMAIL
    payload["recipient"]["id"] = BOT_ID
    payload["id"] = ACTIVITY_ID
    payload["channelId"] = "emulator"  # Required by Bot Framework

    response = await client.post(
        url=STREAM_ENDPOINT,
        json=payload,
    )

    assert response.status_code == 200

    # Wait a bit for streaming to complete
    await asyncio.sleep(2)

    # Debug: Show what we captured
    print(f"\n\nCaptured {len(test_runner.responses)} responses:")
    for i, resp in enumerate(test_runner.responses):
        print(f"  Response {i}: path={resp.path}, text={resp.payload.get('text', 'N/A')}")

    for _ in range(60):
        if len(test_runner.responses) >= 2:
            if test_runner.responses[-1].payload["text"] == "First chunk.\nSecond chunk.":
                break
        await asyncio.sleep(1)
    else:
        last_response = test_runner.responses[-1].payload if test_runner.responses else "NONE"
        pytest.fail(f"Chunks not received in time. Got {len(test_runner.responses)} responses. Last: {last_response}")

    assert test_runner.responses[-1].path.startswith(f"/v3/conversations/{CONVERSATION_ID}/activities/")
    assert test_runner.responses[-1].path != f"/v3/conversations/{CONVERSATION_ID}/activities/{ACTIVITY_ID}"
    assert test_runner.responses[-1].payload["conversation"]["id"] == CONVERSATION_ID
    assert test_runner.responses[-1].payload["from"]["id"] == BOT_ID
    assert test_runner.responses[-1].payload["recipient"]["id"] == USER_ID
    assert test_runner.responses[-1].payload["text"] == "First chunk.\nSecond chunk."
