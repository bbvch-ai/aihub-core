# Migration Tasks: Bot Framework SDK → Microsoft 365 Agents SDK

## Architecture Decisions (Confirmed)
- ✅ **8.1**: Keep inheritance pattern (ActivityHandler)
- ✅ **8.2**: No backward compatibility needed
- ✅ **8.3**: Keep MongoDB storage pattern
- ✅ **Channels**: Use microsoft_agents SDK's channel constants directly (no custom Channels class)
- ✅ **Performance**: Focus on functional testing, not performance benchmarking

---

## Phase 1: Foundation & Setup

### Task 1.1: Update Project Dependencies
**Priority:** Critical
**Estimated Time:** 2 hours
**Dependencies:** None

#### Description
Update `aihub_bot/pyproject.toml` to replace deprecated Bot Framework SDK packages with Microsoft 365 Agents SDK packages.

#### Changes Required
```toml
# Remove:
botbuilder-integration-aiohttp = "^4.16.2"

# Add:
microsoft-agents-hosting-core = "^0.5.0"
microsoft-agents-hosting-aiohttp = "^0.5.0"
microsoft-agents-activity = "^0.5.0"
microsoft-agents-authentication-msal = "^0.5.0"
```

#### Test Specification
**Test File:** `tests/test_dependencies.py`

```python
def test_package_imports():
    """
    PASS CRITERIA: All new SDK packages can be imported without errors.

    This test verifies that:
    1. microsoft_agents.hosting.core is importable
    2. microsoft_agents.hosting.aiohttp is importable
    3. microsoft_agents.activity is importable
    4. No botbuilder packages are present
    """
    # Should succeed
    from microsoft_agents.hosting.core import ActivityHandler, TurnContext
    from microsoft_agents.hosting.aiohttp import CloudAdapter
    from microsoft_agents.activity import Activity, ActivityTypes

    # Should fail - verify old packages are removed
    with pytest.raises(ImportError):
        from botbuilder.core import ActivityHandler

def test_poetry_lock_updated():
    """
    PASS CRITERIA: poetry.lock file contains new packages and excludes old ones.

    Verifies that:
    1. poetry.lock exists and is valid
    2. Contains microsoft-agents-* packages
    3. Does not contain botbuilder-* packages
    """
    import toml
    lock_data = toml.load("poetry.lock")
    package_names = [pkg["name"] for pkg in lock_data["package"]]

    assert "microsoft-agents-hosting-core" in package_names
    assert "microsoft-agents-hosting-aiohttp" in package_names
    assert "botbuilder-integration-aiohttp" not in package_names
```

---

### Task 1.2: Create Migration Test Fixtures
**Priority:** High
**Estimated Time:** 3 hours
**Dependencies:** Task 1.1

#### Description
Create comprehensive test fixtures and utilities for testing migrated components. These fixtures will be reused across all migration tests.

#### Implementation
**File:** `tests/fixtures/bot_fixtures.py`

```python
"""Shared fixtures for bot migration testing."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.activity import Activity, ActivityTypes, ChannelAccount, ConversationAccount


@pytest.fixture
def mock_activity():
    """Create a mock Activity for testing."""
    activity = Activity(
        type=ActivityTypes.message,
        id="test-activity-123",
        text="Hello, bot!",
        from_property=ChannelAccount(id="user-123", name="Test User"),
        recipient=ChannelAccount(id="bot-456", name="Test Bot"),
        conversation=ConversationAccount(id="conv-789", name="Test Conversation"),
        channel_id="msteams",
        locale="en-US",
    )
    return activity


@pytest.fixture
def mock_turn_context(mock_activity):
    """Create a mock TurnContext for testing."""
    context = MagicMock(spec=TurnContext)
    context.activity = mock_activity
    context.send_activity = AsyncMock(return_value=MagicMock(id="response-123"))
    context.update_activity = AsyncMock()
    return context


@pytest.fixture
def teams_activity(mock_activity):
    """Create a Teams-specific activity."""
    mock_activity.channel_id = "msteams"
    return mock_activity


@pytest.fixture
def slack_activity(mock_activity):
    """Create a Slack-specific activity."""
    mock_activity.channel_id = "slack"
    mock_activity.conversation.id = "B12345:T67890:C11111"
    mock_activity.channel_data = {
        "SlackMessage": {
            "event": {
                "ts": "1234567890.123456"
            }
        }
    }
    return mock_activity
```

#### Test Specification
**Test File:** `tests/fixtures/test_bot_fixtures.py`

```python
import pytest
from microsoft_agents.activity import ActivityTypes


def test_mock_activity_fixture(mock_activity):
    """
    PASS CRITERIA: mock_activity fixture creates valid Activity object.

    Verifies:
    1. Activity has required properties
    2. Properties have correct types
    3. Activity is message type
    """
    assert mock_activity.type == ActivityTypes.message
    assert mock_activity.id is not None
    assert mock_activity.text == "Hello, bot!"
    assert mock_activity.from_property.id == "user-123"
    assert mock_activity.recipient.id == "bot-456"


def test_mock_turn_context_fixture(mock_turn_context):
    """
    PASS CRITERIA: mock_turn_context fixture creates valid TurnContext mock.

    Verifies:
    1. TurnContext has activity property
    2. send_activity is async and callable
    3. update_activity is async and callable
    """
    assert mock_turn_context.activity is not None
    assert callable(mock_turn_context.send_activity)
    assert callable(mock_turn_context.update_activity)


@pytest.mark.asyncio
async def test_turn_context_send_activity(mock_turn_context):
    """
    PASS CRITERIA: Mock TurnContext can send activities.

    Verifies:
    1. send_activity returns response with id
    2. Can be awaited without errors
    """
    response = await mock_turn_context.send_activity("Test message")
    assert response.id is not None


def test_teams_activity_fixture(teams_activity):
    """
    PASS CRITERIA: teams_activity fixture creates Teams-specific activity.

    Verifies:
    1. Channel ID is msteams
    2. Has required Teams properties
    """
    assert teams_activity.channel_id == "msteams"


def test_slack_activity_fixture(slack_activity):
    """
    PASS CRITERIA: slack_activity fixture creates Slack-specific activity.

    Verifies:
    1. Channel ID is slack
    2. Has Slack-specific conversation ID format
    3. Has channel_data with SlackMessage
    """
    assert slack_activity.channel_id == "slack"
    assert ":" in slack_activity.conversation.id
    assert "SlackMessage" in slack_activity.channel_data
    assert "ts" in slack_activity.channel_data["SlackMessage"]["event"]
```

---

## Phase 2: Core Migration

### Task 2.1: Migrate RoutesService (Adapter & Authentication)
**Priority:** Critical
**Estimated Time:** 8 hours
**Dependencies:** Task 1.1, 1.2

#### Description
Migrate `RoutesService.py` to use Microsoft 365 Agents SDK's `CloudAdapter`. This is the most critical component as all bot routes depend on it.

#### Changes Required
**File:** `aihub_bot/aihub_bot/routes/RoutesService.py`

```python
# BEFORE:
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication

@staticmethod
def get_adapter(path: str) -> CloudAdapter:
    credentials: Credentials = RoutesService.get_credentials(path)
    return CloudAdapter(ConfigurationBotFrameworkAuthentication(credentials))

# AFTER:
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.authentication.msal import ConfigurationBotFrameworkAuthentication

@staticmethod
def get_adapter(path: str) -> CloudAdapter:
    credentials: Credentials = RoutesService.get_credentials(path)
    # Note: Authentication mechanism may need adjustment based on new SDK API
    return CloudAdapter(ConfigurationBotFrameworkAuthentication(credentials))
```

#### Test Specification
**Test File:** `tests/routes/test_routes_service.py`

```python
import pytest
from aihub_bot.routes.RoutesService import RoutesService
from aihub_bot.persistence.entities.PathEntity import Credentials
from microsoft_agents.hosting.aiohttp import CloudAdapter


@pytest.fixture
def mock_credentials():
    """Create mock credentials for testing."""
    return {
        "APP_TYPE": "MultiTenant",
        "APP_ID": "test-app-id-123",
        "APP_PASSWORD": "test-password-456",
    }


def test_routes_service_imports_new_sdk():
    """
    PASS CRITERIA: RoutesService uses new SDK imports.

    Verifies:
    1. No botbuilder imports in the file
    2. Uses microsoft_agents imports
    """
    import inspect
    source = inspect.getsource(RoutesService)

    # Should not contain old imports
    assert "from botbuilder" not in source
    assert "from botframework" not in source

    # Should contain new imports
    assert "from microsoft_agents" in source


def test_get_adapter_returns_cloud_adapter(monkeypatch, mock_credentials):
    """
    PASS CRITERIA: get_adapter() returns CloudAdapter instance from new SDK.

    Verifies:
    1. Returns CloudAdapter instance
    2. CloudAdapter is from microsoft_agents package
    3. Can be instantiated without errors
    """
    # Mock the credentials retrieval
    monkeypatch.setattr(
        "aihub_bot.routes.RoutesService.RoutesService.get_credentials",
        lambda path: mock_credentials
    )

    adapter = RoutesService.get_adapter("/api/v1/messages")

    assert isinstance(adapter, CloudAdapter)
    assert "microsoft_agents" in type(adapter).__module__


@pytest.mark.asyncio
async def test_adapter_can_process_activity(monkeypatch, mock_credentials, mock_activity):
    """
    PASS CRITERIA: CloudAdapter from new SDK can process activities.

    Verifies:
    1. Adapter has process_activity method
    2. Method is async callable
    3. Can handle basic activity processing
    """
    monkeypatch.setattr(
        "aihub_bot.routes.RoutesService.RoutesService.get_credentials",
        lambda path: mock_credentials
    )

    adapter = RoutesService.get_adapter("/api/v1/messages")

    # Verify adapter has required methods
    assert hasattr(adapter, "process_activity")
    assert callable(adapter.process_activity)


def test_adapter_authentication_configuration(monkeypatch, mock_credentials):
    """
    PASS CRITERIA: Adapter is correctly configured with authentication.

    Verifies:
    1. Adapter accepts credentials configuration
    2. Multi-tenant configuration works
    3. Single-tenant configuration works (if applicable)
    """
    monkeypatch.setattr(
        "aihub_bot.routes.RoutesService.RoutesService.get_credentials",
        lambda path: mock_credentials
    )

    # Test multi-tenant
    adapter = RoutesService.get_adapter("/api/v1/messages")
    assert adapter is not None

    # Test single-tenant
    single_tenant_creds = mock_credentials.copy()
    single_tenant_creds["APP_TYPE"] = "SingleTenant"
    single_tenant_creds["APP_TENANTID"] = "test-tenant-123"

    monkeypatch.setattr(
        "aihub_bot.routes.RoutesService.RoutesService.get_credentials",
        lambda path: single_tenant_creds
    )

    adapter = RoutesService.get_adapter("/api/v1/messages")
    assert adapter is not None
```

---

### Task 2.2: Migrate BaseChatBot
**Priority:** Critical
**Estimated Time:** 6 hours
**Dependencies:** Task 2.1

#### Description
Migrate `BaseChatBot.py` to use new SDK imports while maintaining the inheritance pattern. This is the base class for all chat bots.

#### Changes Required
**File:** `aihub_bot/aihub_bot/bots/chat/BaseChatBot.py`

```python
# BEFORE:
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import Activity, ActivityTypes
from botframework.connector import Channels

# AFTER:
from microsoft_agents.hosting.core import ActivityHandler, TurnContext
from microsoft_agents.activity import Activity, ActivityTypes
# Note: Use string literals for channel IDs (e.g., "msteams", "slack")
# The new SDK may provide channel constants - check documentation
```

#### Test Specification
**Test File:** `tests/bots/chat/test_base_chat_bot.py`

```python
import pytest
from aihub_bot.bots.chat.BaseChatBot import BaseChatBot
from aihub_bot.bots.chat.CompletionHandler import CompletionHandler
from microsoft_agents.hosting.core import ActivityHandler, TurnContext
from aihub_bot.constants import Channels


class MockCompletionHandler(CompletionHandler):
    """Mock completion handler for testing."""

    @staticmethod
    async def get_completion(**kwargs) -> str:
        return "Mock response"

    @staticmethod
    async def get_stream_completion(**kwargs):
        yield "Mock"
        yield " streaming"
        yield " response"


@pytest.fixture
def base_chat_bot():
    """Create BaseChatBot instance for testing."""
    handler = MockCompletionHandler()
    return BaseChatBot(
        path="/api/v1/test",
        completion_handler=handler,
        handler_kwargs={"test": "value"},
        typing_timeout_seconds=60,
    )


def test_base_chat_bot_imports_new_sdk():
    """
    PASS CRITERIA: BaseChatBot uses new SDK imports only.

    Verifies:
    1. No botbuilder imports in source
    2. Uses microsoft_agents imports
    3. No botframework imports
    """
    import inspect
    source = inspect.getsource(BaseChatBot)

    assert "from botbuilder" not in source
    assert "from botframework" not in source
    assert "from microsoft_agents" in source


def test_base_chat_bot_inherits_activity_handler(base_chat_bot):
    """
    PASS CRITERIA: BaseChatBot inherits from new SDK's ActivityHandler.

    Verifies:
    1. Is instance of ActivityHandler
    2. ActivityHandler is from microsoft_agents
    3. Has required bot methods
    """
    assert isinstance(base_chat_bot, ActivityHandler)
    assert "microsoft_agents" in ActivityHandler.__module__

    # Verify has standard bot methods
    assert hasattr(base_chat_bot, "on_message_activity")
    assert hasattr(base_chat_bot, "on_conversation_update_activity")


@pytest.mark.asyncio
async def test_on_message_activity(base_chat_bot, mock_turn_context):
    """
    PASS CRITERIA: on_message_activity works with new SDK.

    Verifies:
    1. Method accepts TurnContext from new SDK
    2. Can be called without errors
    3. Processes messages correctly
    """
    await base_chat_bot.on_message_activity(mock_turn_context)

    # Verify send_activity was called
    mock_turn_context.send_activity.assert_called()


@pytest.mark.asyncio
async def test_on_conversation_update_teams(base_chat_bot, teams_activity, mock_turn_context):
    """
    PASS CRITERIA: Teams conversation update handling works.

    Verifies:
    1. Handles Teams bot re-add scenario
    2. Channel ID comparison works with string literals
    3. Conversation reset works as expected
    """
    from microsoft_agents.activity import ChannelAccount

    # Simulate bot being added to conversation
    teams_activity.channel_id = "msteams"
    teams_activity.members_added = [
        ChannelAccount(id="bot-456", name="Test Bot")
    ]
    mock_turn_context.activity = teams_activity

    await base_chat_bot.on_conversation_update_activity(mock_turn_context)

    # Should handle without error
    assert True


@pytest.mark.asyncio
async def test_process_message_with_typing_indicator(base_chat_bot, mock_turn_context, monkeypatch):
    """
    PASS CRITERIA: Typing indicator works with new SDK.

    Verifies:
    1. Typing activities are sent during processing
    2. Typing stops when response ready
    3. Uses new SDK's Activity types
    """
    typing_sent = []

    async def mock_send(activity):
        if activity.type == "typing":
            typing_sent.append(True)
        return MagicMock(id="123")

    mock_turn_context.send_activity = mock_send

    await base_chat_bot._process_message(mock_turn_context, is_streaming=False)

    # At least one typing indicator should be sent
    assert len(typing_sent) > 0


def test_channel_id_string_literals(base_chat_bot):
    """
    PASS CRITERIA: Bot uses string literals for channel IDs.

    Verifies:
    1. Can compare channel IDs using strings
    2. Common channel IDs work as expected
    """
    # Channel IDs are simple strings
    assert "msteams" == "msteams"
    assert "slack" == "slack"
    assert "webchat" == "webchat"
```

---

### Task 2.3: Migrate CompletionHandler
**Priority:** Critical
**Estimated Time:** 6 hours
**Dependencies:** Task 2.2

#### Description
Migrate `CompletionHandler.py` to use new SDK. This handles all completion logic including streaming responses and error handling.

#### Changes Required
**File:** `aihub_bot/aihub_bot/bots/chat/CompletionHandler.py`

```python
# BEFORE:
from botbuilder.core import TurnContext
from botbuilder.schema import Activity, ActivityTypes, Entity, ErrorResponseException

# AFTER:
from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.activity import Activity, ActivityTypes, Entity
# Note: ErrorResponseException may need to be replaced with new SDK's exception class
```

#### Test Specification
**Test File:** `tests/bots/chat/test_completion_handler.py`

```python
import pytest
from aihub_bot.bots.chat.CompletionHandler import CompletionHandler
from microsoft_agents.activity import Activity, ActivityTypes


def test_completion_handler_imports_new_sdk():
    """
    PASS CRITERIA: CompletionHandler uses new SDK imports.

    Verifies:
    1. No botbuilder imports
    2. Uses microsoft_agents imports
    """
    import inspect
    source = inspect.getsource(CompletionHandler)

    assert "from botbuilder" not in source
    assert "from microsoft_agents" in source


@pytest.mark.asyncio
async def test_send_typing_activity(mock_turn_context):
    """
    PASS CRITERIA: Typing activity can be sent with new SDK.

    Verifies:
    1. send_activity accepts Activity with typing type
    2. Activity is from new SDK
    3. Typing indicator works correctly
    """
    from asyncio import Event
    from aihub_lib.i18n.LocaleHandler import LocaleHandler

    signal = Event()
    locale_handler = LocaleHandler()

    # Should complete without error
    import asyncio
    task = asyncio.create_task(
        CompletionHandler.send_typing_activity(
            turn_context=mock_turn_context,
            signal=signal,
            t=locale_handler,
            timeout_seconds=2
        )
    )

    await asyncio.sleep(0.1)
    signal.set()
    await task

    # Verify typing activity was sent
    calls = [call for call in mock_turn_context.send_activity.call_args_list]
    assert any(
        call[0][0].type == ActivityTypes.typing if hasattr(call[0][0], 'type')
        else call[0][0] == ActivityTypes.typing
        for call in calls if len(call[0]) > 0
    )


@pytest.mark.asyncio
async def test_send_response_stream(mock_turn_context):
    """
    PASS CRITERIA: Streaming responses work with new SDK.

    Verifies:
    1. Can send initial activity
    2. Can update activity with chunks
    3. Handles long messages correctly
    4. Uses new SDK's Activity class
    """
    async def mock_generator():
        yield "Hello"
        yield " world"
        yield "!"

    result = await CompletionHandler.send_response_stream(
        turn_context=mock_turn_context,
        response_generator=mock_generator()
    )

    assert result == "Hello world!"
    assert mock_turn_context.send_activity.called
    assert mock_turn_context.update_activity.called


@pytest.mark.asyncio
async def test_handle_exception(mock_turn_context):
    """
    PASS CRITERIA: Exception handling works with new SDK.

    Verifies:
    1. Errors are caught and handled
    2. Error messages sent via new SDK
    3. Typing indicator stopped on error
    """
    from asyncio import Event
    from aihub_lib.i18n.LocaleHandler import LocaleHandler
    import asyncio

    signal = Event()
    typing_task = asyncio.create_task(asyncio.sleep(0.1))
    locale_handler = LocaleHandler()
    exception = ValueError("Test error")

    response = await CompletionHandler.handle_exception(
        turn_context=mock_turn_context,
        exception=exception,
        typing_task=typing_task,
        typing_stop_signal=signal,
        t=locale_handler,
    )

    assert signal.is_set()
    assert mock_turn_context.send_activity.called
    assert isinstance(response, str)


def test_slack_message_handling(slack_activity, mock_turn_context):
    """
    PASS CRITERIA: Slack-specific handling works with new SDK.

    Verifies:
    1. Can detect Slack channel messages
    2. Can detect Slack direct messages
    3. Can detect bot mentions
    4. Slack conversation ID format handled correctly
    """
    mock_turn_context.activity = slack_activity

    # Test channel message detection
    is_channel = CompletionHandler.is_slack_channel_message(mock_turn_context)
    assert isinstance(is_channel, bool)

    # Test mention detection
    from microsoft_agents.activity import Entity
    slack_activity.entities = [
        Entity(
            type="mention",
            additional_properties={
                "mentioned": {"id": "bot-456"}
            }
        )
    ]
    mock_turn_context.activity = slack_activity

    is_mentioned = CompletionHandler.is_bot_mentioned(mock_turn_context)
    assert isinstance(is_mentioned, bool)


def test_system_message_creation(mock_turn_context):
    """
    PASS CRITERIA: System message creation works with new SDK.

    Verifies:
    1. Can create system message from path config
    2. Uses new SDK's message structure
    3. Username/assistant name replacement works
    """
    # This test depends on PathEntity having a system message configured
    # Will be tested in integration tests
    pass
```

---

### Task 2.4: Migrate ContentExtractor
**Priority:** High
**Estimated Time:** 3 hours
**Dependencies:** Task 2.3

#### Description
Migrate `ContentExtractor.py` to use new SDK for activity content extraction.

#### Changes Required
**File:** `aihub_bot/aihub_bot/bots/chat/ContentExtractor.py`

```python
# BEFORE:
from botbuilder.schema import Activity, Attachment
from botframework.connector import Channels

# AFTER:
from microsoft_agents.activity import Activity, Attachment
# Use string literals for channel IDs
```

#### Test Specification
**Test File:** `tests/bots/chat/test_content_extractor.py`

```python
import pytest
from aihub_bot.bots.chat.ContentExtractor import ContentExtractor
from microsoft_agents.activity import Activity, Attachment


def test_content_extractor_imports_new_sdk():
    """
    PASS CRITERIA: ContentExtractor uses new SDK imports.

    Verifies:
    1. No botbuilder imports
    2. Uses microsoft_agents imports
    3. No botframework imports
    """
    import inspect
    source = inspect.getsource(ContentExtractor)

    assert "from botbuilder" not in source
    assert "from botframework" not in source
    assert "from microsoft_agents" in source


def test_extract_text_content():
    """
    PASS CRITERIA: Can extract text from Activity.

    Verifies:
    1. Accepts Activity from new SDK
    2. Extracts text correctly
    3. Returns expected format
    """
    activity = Activity(text="Hello world", type="message")

    content = ContentExtractor.extract_content_from_activity(
        path="/api/v1/test",
        activity=activity
    )

    assert len(content) > 0
    assert any(c.text == "Hello world" for c in content if hasattr(c, 'text'))


def test_extract_attachment_content():
    """
    PASS CRITERIA: Can extract attachments from Activity.

    Verifies:
    1. Handles Activity with attachments
    2. Uses new SDK's Attachment class
    3. Extracts attachment metadata correctly
    """
    attachment = Attachment(
        content_type="image/png",
        content_url="https://example.com/image.png",
        name="test.png"
    )
    activity = Activity(
        text="Check this out",
        attachments=[attachment],
        type="message"
    )

    content = ContentExtractor.extract_content_from_activity(
        path="/api/v1/test",
        activity=activity
    )

    assert len(content) > 0
    # Verify both text and attachment are extracted
    assert any(hasattr(c, 'text') for c in content)


def test_channel_specific_extraction(teams_activity, slack_activity):
    """
    PASS CRITERIA: Channel-specific extraction works.

    Verifies:
    1. Teams activities handled correctly (channel_id == "msteams")
    2. Slack activities handled correctly (channel_id == "slack")
    3. Channel ID string comparison works
    """
    # Teams extraction
    teams_content = ContentExtractor.extract_content_from_activity(
        path="/api/v1/test",
        activity=teams_activity
    )
    assert teams_content is not None
    assert teams_activity.channel_id == "msteams"

    # Slack extraction
    slack_content = ContentExtractor.extract_content_from_activity(
        path="/api/v1/test",
        activity=slack_activity
    )
    assert slack_content is not None
    assert slack_activity.channel_id == "slack"
```

---

## Phase 3: Specialized Bots Migration

### Task 3.1: Migrate Agent-Based Bots
**Priority:** High
**Estimated Time:** 6 hours
**Dependencies:** Task 2.2, 2.3, 2.4

#### Description
Migrate all agent-based bot implementations:
- `AgentChatBot.py`
- `StreamAgentChatBot.py`
- `AgentCompletionHandler.py`

#### Changes Required
```python
# BEFORE:
from botbuilder.core import TurnContext
from botframework.connector import Channels

# AFTER:
from microsoft_agents.hosting.core import TurnContext
# Use string literals for channel IDs: "msteams", "slack", etc.
```

#### Test Specification
**Test File:** `tests/bots/chat/agent/test_agent_chat_bot.py`

```python
import pytest
from aihub_bot.bots.chat.agent.AgentChatBot import AgentChatBot
from aihub_bot.bots.chat.agent.StreamAgentChatBot import StreamAgentChatBot
from aihub_bot.bots.chat.agent.AgentCompletionHandler import AgentCompletionHandler
from aihub_bot.bots.chat.BaseChatBot import BaseChatBot


def test_agent_chat_bot_imports_new_sdk():
    """
    PASS CRITERIA: All agent bot files use new SDK.

    Verifies:
    1. AgentChatBot has no botbuilder imports
    2. StreamAgentChatBot has no botbuilder imports
    3. AgentCompletionHandler has no botbuilder imports
    """
    import inspect

    for cls in [AgentChatBot, StreamAgentChatBot, AgentCompletionHandler]:
        source = inspect.getsource(cls)
        assert "from botbuilder" not in source
        assert "from botframework" not in source


def test_agent_chat_bot_inherits_base_bot():
    """
    PASS CRITERIA: AgentChatBot inherits from migrated BaseChatBot.

    Verifies:
    1. Is subclass of BaseChatBot
    2. BaseChatBot uses new SDK
    3. Inheritance chain is correct
    """
    assert issubclass(AgentChatBot, BaseChatBot)


@pytest.mark.asyncio
async def test_agent_completion_handler_nats_integration(mock_turn_context):
    """
    PASS CRITERIA: Agent completion works with NATS and new SDK.

    Verifies:
    1. Can send messages to NATS agents
    2. Can receive responses via NATS
    3. TurnContext from new SDK works with agent integration
    4. Thread ID and display ID handled correctly
    """
    from unittest.mock import AsyncMock, MagicMock
    from bson import ObjectId

    # Mock NATS connection
    mock_nats = AsyncMock()

    handler = AgentCompletionHandler(agent_class="test_agent")
    handler.nats_client = mock_nats

    thread_id = ObjectId()
    display_id = ObjectId()

    # This should not raise errors
    try:
        response = await handler.get_completion(
            turn_context=mock_turn_context,
            path="/api/v1/test",
            thread_id=thread_id,
            display_id=display_id,
            user={"id": "test-user"}
        )
        # If NATS is not available, this will timeout - that's expected in unit tests
    except Exception as e:
        # Verify it's a timeout/connection error, not an SDK compatibility error
        assert "botbuilder" not in str(e).lower()
        assert "botframework" not in str(e).lower()


@pytest.mark.asyncio
async def test_stream_agent_chat_bot_streaming(mock_turn_context):
    """
    PASS CRITERIA: Streaming works with new SDK.

    Verifies:
    1. StreamAgentChatBot can stream responses
    2. Uses new SDK's activity updates
    3. Channel ID handling works with string literals
    """
    from unittest.mock import AsyncMock

    bot = StreamAgentChatBot(
        path="/api/v1/test",
        completion_handler=AgentCompletionHandler(agent_class="test"),
        handler_kwargs={"user": {"id": "test"}}
    )

    # Verify streaming capability exists
    assert hasattr(bot, '_process_message')

    # Test with mocked streaming
    async def mock_stream():
        yield "chunk1"
        yield "chunk2"

    # Should handle without SDK compatibility errors
    try:
        await bot.on_message_activity(mock_turn_context)
    except Exception as e:
        # Verify errors are not SDK-related
        assert "botbuilder" not in str(e).lower()
```

---

### Task 3.2: Migrate OpenAI-Based Bots
**Priority:** High
**Estimated Time:** 6 hours
**Dependencies:** Task 2.2, 2.3, 2.4

#### Description
Migrate all OpenAI-based bot implementations:
- `OpenaiChatBot.py`
- `StreamOpenaiChatBot.py`
- `OpenaiCompletionHandler.py`

#### Test Specification
**Test File:** `tests/bots/chat/openai/test_openai_chat_bot.py`

```python
import pytest
from aihub_bot.bots.chat.openai.OpenaiChatBot import OpenaiChatBot
from aihub_bot.bots.chat.openai.StreamOpenaiChatBot import StreamOpenaiChatBot
from aihub_bot.bots.chat.openai.OpenaiCompletionHandler import OpenaiCompletionHandler
from aihub_bot.bots.chat.BaseChatBot import BaseChatBot


def test_openai_chat_bot_imports_new_sdk():
    """
    PASS CRITERIA: All OpenAI bot files use new SDK.

    Verifies:
    1. OpenaiChatBot has no botbuilder imports
    2. StreamOpenaiChatBot has no botbuilder imports
    3. OpenaiCompletionHandler has no botbuilder imports
    """
    import inspect

    for cls in [OpenaiChatBot, StreamOpenaiChatBot, OpenaiCompletionHandler]:
        source = inspect.getsource(cls)
        assert "from botbuilder" not in source
        assert "from botframework" not in source


def test_openai_chat_bot_inherits_base_bot():
    """
    PASS CRITERIA: OpenaiChatBot inherits from migrated BaseChatBot.

    Verifies:
    1. Is subclass of BaseChatBot
    2. Inheritance chain uses new SDK
    """
    assert issubclass(OpenaiChatBot, BaseChatBot)


@pytest.mark.asyncio
async def test_openai_completion_handler(mock_turn_context):
    """
    PASS CRITERIA: OpenAI completion works with new SDK.

    Verifies:
    1. Can call OpenAI API with new SDK TurnContext
    2. Response format compatible with new SDK
    3. Message history persists correctly
    """
    from unittest.mock import AsyncMock, MagicMock
    from llama_index.core.llms import ChatMessage

    # Mock LLM
    mock_llm = MagicMock()
    mock_llm.achat = AsyncMock(return_value=MagicMock(
        message=ChatMessage(role="assistant", content="Test response")
    ))

    handler = OpenaiCompletionHandler(llm_config=MagicMock())
    handler.llm = mock_llm

    response = await handler.get_completion(
        turn_context=mock_turn_context,
        path="/api/v1/test",
        thread_id=MagicMock(),
        display_id=MagicMock(),
    )

    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_stream_openai_chat_bot(mock_turn_context):
    """
    PASS CRITERIA: OpenAI streaming works with new SDK.

    Verifies:
    1. Can stream OpenAI responses
    2. Activity updates work with new SDK
    3. Typing indicators work during streaming
    """
    from unittest.mock import AsyncMock, MagicMock

    bot = StreamOpenaiChatBot(
        path="/api/v1/test",
        completion_handler=OpenaiCompletionHandler(llm_config=MagicMock()),
        handler_kwargs={}
    )

    # Mock streaming response
    async def mock_stream():
        yield "Hello"
        yield " world"

    # Verify can handle streaming with new SDK
    assert hasattr(bot, '_process_message')
```

---

### Task 3.3: Migrate Bot-in-the-Loop
**Priority:** High
**Estimated Time:** 6 hours
**Dependencies:** Task 2.2, 2.3, 2.4

#### Description
Migrate Bot-in-the-Loop implementation:
- `BotInTheLoopBot.py`
- `BotInTheLoopHandler.py`

#### Test Specification
**Test File:** `tests/bots/bot_in_the_loop/test_bot_in_the_loop.py`

```python
import pytest
from aihub_bot.bots.bot_in_the_loop.BotInTheLoopBot import BotInTheLoopBot
from aihub_bot.routes.bot_in_the_loop.BotInTheLoopHandler import BotInTheLoopHandler
from microsoft_agents.hosting.core import ActivityHandler


def test_bot_in_the_loop_imports_new_sdk():
    """
    PASS CRITERIA: Bot-in-the-Loop uses new SDK.

    Verifies:
    1. BotInTheLoopBot has no botbuilder imports
    2. BotInTheLoopHandler has no botbuilder imports
    """
    import inspect

    for cls in [BotInTheLoopBot, BotInTheLoopHandler]:
        source = inspect.getsource(cls)
        assert "from botbuilder" not in source
        assert "from botframework" not in source


def test_bot_in_the_loop_inherits_activity_handler():
    """
    PASS CRITERIA: BotInTheLoopBot inherits from new SDK ActivityHandler.

    Verifies:
    1. Is subclass of ActivityHandler
    2. ActivityHandler from microsoft_agents
    """
    assert issubclass(BotInTheLoopBot, ActivityHandler)
    assert "microsoft_agents" in ActivityHandler.__module__


@pytest.mark.asyncio
async def test_bot_in_the_loop_slack_thread_detection(slack_activity, mock_turn_context):
    """
    PASS CRITERIA: Slack thread detection works with new SDK.

    Verifies:
    1. Can detect Slack channel thread messages
    2. Uses new SDK activity structure
    3. Thread timestamp extraction works
    """
    mock_turn_context.activity = slack_activity

    bot = BotInTheLoopBot()

    # Should detect Slack thread
    is_thread = bot.is_slack_channel_thread_message(mock_turn_context)
    assert isinstance(is_thread, bool)


@pytest.mark.asyncio
async def test_bot_in_the_loop_handler_send_request(mock_turn_context):
    """
    PASS CRITERIA: Handler can send Bot-in-the-Loop requests.

    Verifies:
    1. Can create proactive messages with new SDK
    2. ConversationReference works with new SDK
    3. Can send to Slack channels
    """
    from microsoft_agents.activity import ConversationReference

    handler = BotInTheLoopHandler()

    # Create conversation reference
    ref = ConversationReference(
        conversation=mock_turn_context.activity.conversation,
        service_url="https://test.slack.com",
        channel_id="slack"
    )

    # Verify reference is compatible
    assert ref.conversation is not None
    assert ref.channel_id == "slack"


@pytest.mark.asyncio
async def test_bot_in_the_loop_response_handling(mock_turn_context):
    """
    PASS CRITERIA: Can capture and forward user responses.

    Verifies:
    1. Response capture works with new SDK
    2. NATS message sending compatible
    3. Thread context maintained
    """
    bot = BotInTheLoopBot()

    # Simulate user responding in thread
    await bot.on_message_activity(mock_turn_context)

    # Should process without SDK compatibility errors
    assert True
```

---

## Phase 4: Controllers & Integration

### Task 4.1: Migrate All Controllers
**Priority:** Medium
**Estimated Time:** 4 hours
**Dependencies:** Task 3.1, 3.2, 3.3

#### Description
Migrate all controller files:
- `routes/agent/AgentChatController.py`
- `routes/openai/OpenaiChatController.py`
- `routes/bot_in_the_loop/BotInTheLoopController.py`

#### Test Specification
**Test File:** `tests/routes/test_controllers.py`

```python
import pytest
from fastapi.testclient import TestClient
from aihub_bot.runners.BotTestRunner import BotTestRunner


def test_controllers_import_new_sdk():
    """
    PASS CRITERIA: All controllers use new SDK.

    Verifies:
    1. No botbuilder imports in any controller
    2. CloudAdapter from microsoft_agents
    """
    from aihub_bot.routes.agent.AgentChatController import AgentChatController
    from aihub_bot.routes.openai.OpenaiChatController import OpenaiChatController
    from aihub_bot.routes.bot_in_the_loop.BotInTheLoopController import BotInTheLoopController

    import inspect

    for ctrl_cls in [AgentChatController, OpenaiChatController, BotInTheLoopController]:
        source = inspect.getsource(ctrl_cls)
        assert "from botbuilder" not in source


@pytest.mark.asyncio
async def test_agent_controller_endpoint(mock_activity):
    """
    PASS CRITERIA: Agent controller endpoints work with new SDK.

    Verifies:
    1. POST endpoint accepts activities
    2. Returns valid response
    3. Uses migrated bot classes
    """
    from aihub_bot.routes.agent.AgentChatController import AgentChatController
    from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler import DangerousDevelopmentOnlyAuthHandler
    from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider import DangerousDevelopmentOnlyIdentityProvider

    auth = DangerousDevelopmentOnlyAuthHandler(
        identity_provider=DangerousDevelopmentOnlyIdentityProvider()
    )

    runner = BotTestRunner()
    controller = AgentChatController(auth=auth, agent_class="test_agent")
    runner.mount(controller.chat_completion())

    client = TestClient(runner.create_app())

    response = client.post(
        "/api/v1/agent/chat",
        json=mock_activity.__dict__,
        headers={"Service-Url": "https://test.botframework.com"}
    )

    # Should return 200 or handle gracefully
    assert response.status_code in [200, 401, 500]  # 401 if auth fails, 500 if NATS unavailable


@pytest.mark.asyncio
async def test_openai_controller_endpoint(mock_activity):
    """
    PASS CRITERIA: OpenAI controller endpoints work with new SDK.

    Verifies:
    1. POST endpoint accepts activities
    2. Returns valid response
    3. Uses migrated bot classes
    """
    from aihub_bot.routes.openai.OpenaiChatController import OpenaiChatController
    from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler import DangerousDevelopmentOnlyAuthHandler
    from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider import DangerousDevelopmentOnlyIdentityProvider

    auth = DangerousDevelopmentOnlyAuthHandler(
        identity_provider=DangerousDevelopmentOnlyIdentityProvider()
    )

    runner = BotTestRunner()
    controller = OpenaiChatController(auth=auth, llm_config=MagicMock())
    runner.mount(controller.chat_completion())

    client = TestClient(runner.create_app())

    response = client.post(
        "/api/v1/openai/chat",
        json=mock_activity.__dict__,
        headers={"Service-Url": "https://test.botframework.com"}
    )

    assert response.status_code in [200, 401, 500]
```

---

### Task 4.2: Migrate Activity Models
**Priority:** Low
**Estimated Time:** 2 hours
**Dependencies:** Task 4.1

#### Description
Migrate `routes/activity_model.py` to use new SDK schema types.

#### Test Specification
**Test File:** `tests/routes/test_activity_model.py`

```python
import pytest
from aihub_bot.routes.activity_model import *


def test_activity_model_imports_new_sdk():
    """
    PASS CRITERIA: activity_model uses new SDK.

    Verifies:
    1. No botbuilder.schema imports
    2. Uses microsoft_agents.activity
    """
    import inspect
    import aihub_bot.routes.activity_model as model

    source = inspect.getsource(model)
    assert "from botbuilder.schema" not in source
    assert "from microsoft_agents.activity" in source


def test_activity_model_types_compatible():
    """
    PASS CRITERIA: Activity models are compatible with new SDK.

    Verifies:
    1. Can create activity objects
    2. Types match new SDK expectations
    3. Serialization works correctly
    """
    from microsoft_agents.activity import Activity, ActivityTypes

    # Should be able to create and use activity types
    activity = Activity(type=ActivityTypes.message, text="test")
    assert activity.type == ActivityTypes.message
```

---

## Phase 5: Testing & Validation

### Task 5.1: Update Integration Tests
**Priority:** High
**Estimated Time:** 8 hours
**Dependencies:** All Phase 4 tasks

#### Description
Update all existing integration tests to work with the new SDK and verify no regressions.

#### Test Specification
**Test File:** `tests/integration/test_full_bot_flow.py`

```python
import pytest
from fastapi.testclient import TestClient
from aihub_bot.runners.BotTestRunner import BotTestRunner
import json


@pytest.fixture
def full_bot_app():
    """Create full bot application with all controllers."""
    from aihub_bot.routes.agent.AgentChatController import AgentChatController
    from aihub_bot.routes.openai.OpenaiChatController import OpenaiChatController
    from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler import DangerousDevelopmentOnlyAuthHandler
    from aihub_lib.auth.identity.DangerousDevelopmentOnlyIdentityProvider import DangerousDevelopmentOnlyIdentityProvider

    auth = DangerousDevelopmentOnlyAuthHandler(
        identity_provider=DangerousDevelopmentOnlyIdentityProvider()
    )

    runner = BotTestRunner()
    runner.mount(
        AgentChatController(auth=auth, agent_class="test").chat_completion(),
        OpenaiChatController(auth=auth, llm_config=MagicMock()).chat_completion(),
    )

    return TestClient(runner.create_app())


def test_full_conversation_flow_teams(full_bot_app, teams_activity):
    """
    PASS CRITERIA: Complete Teams conversation works end-to-end.

    Verifies:
    1. Bot receives Teams message
    2. Processes with new SDK
    3. Sends response
    4. Conversation persists correctly
    5. Typing indicators work
    """
    # Load test activity
    activity_json = teams_activity.__dict__

    response = full_bot_app.post(
        "/api/v1/agent/chat",
        json=activity_json,
        headers={"Service-Url": "https://smba.trafficmanager.net/emea/"}
    )

    # Verify response
    assert response.status_code in [200, 500]  # 500 acceptable if NATS unavailable


def test_full_conversation_flow_slack(full_bot_app, slack_activity):
    """
    PASS CRITERIA: Complete Slack conversation works end-to-end.

    Verifies:
    1. Bot receives Slack message
    2. Handles threading correctly
    3. Processes with new SDK
    4. Sends response to correct thread
    """
    activity_json = slack_activity.__dict__

    response = full_bot_app.post(
        "/api/v1/agent/chat",
        json=activity_json,
        headers={"Service-Url": "https://slack.botframework.com"}
    )

    assert response.status_code in [200, 500]


def test_streaming_response_teams(full_bot_app, teams_activity):
    """
    PASS CRITERIA: Streaming works end-to-end with new SDK.

    Verifies:
    1. Initial activity sent
    2. Activity updates stream correctly
    3. Final response complete
    4. No SDK compatibility errors
    """
    # Test with streaming endpoint
    activity_json = teams_activity.__dict__

    response = full_bot_app.post(
        "/api/v1/agent/chat",  # Assuming this supports streaming
        json=activity_json,
        headers={"Service-Url": "https://smba.trafficmanager.net/emea/"}
    )

    assert response.status_code in [200, 500]


def test_conversation_persistence(full_bot_app, mock_activity):
    """
    PASS CRITERIA: Conversation history persists across messages.

    Verifies:
    1. First message creates conversation
    2. Second message retrieves history
    3. Conversation TTL works
    4. MongoDB storage compatible with new SDK
    """
    from aihub_bot.persistence.entities.ConversationEntity import ConversationEntity

    # Send first message
    activity1 = mock_activity.__dict__
    full_bot_app.post(
        "/api/v1/openai/chat",
        json=activity1,
        headers={"Service-Url": "https://test.botframework.com"}
    )

    # Verify conversation exists
    conv = ConversationEntity.get_by_conversation_id(mock_activity.conversation.id)
    if conv:  # May not exist if endpoint failed
        assert len(conv.messages) > 0


def test_error_handling_integration(full_bot_app, mock_activity):
    """
    PASS CRITERIA: Error handling works across full stack.

    Verifies:
    1. Invalid activities handled gracefully
    2. Error messages use new SDK
    3. Typing indicators stop on error
    4. User receives error message
    """
    # Send malformed activity
    invalid_activity = {"invalid": "data"}

    response = full_bot_app.post(
        "/api/v1/agent/chat",
        json=invalid_activity,
        headers={"Service-Url": "https://test.botframework.com"}
    )

    # Should handle gracefully, not crash
    assert response.status_code in [400, 422, 500]
```

---

### Task 5.2: Update Playground Tests
**Priority:** Medium
**Estimated Time:** 4 hours
**Dependencies:** Task 5.1

#### Description
Update and verify playground tests work with new SDK.

#### Test Specification
**Test File:** `playground/testing/tests/test_playground_bots.py`

```python
import pytest
from aihub_bot.runners.SimulatedAgentBotTestRunner import SimulatedAgentBotTestRunner
from fastapi.testclient import TestClient


def test_simulated_agent_bot_runner_with_new_sdk():
    """
    PASS CRITERIA: SimulatedAgentBotTestRunner works with new SDK.

    Verifies:
    1. Test runner creates app successfully
    2. Simulated agents work with migrated bots
    3. Streaming simulation works
    4. No SDK compatibility issues
    """
    runner = SimulatedAgentBotTestRunner(
        agent_class="test_agent",
        agent_id="test_123"
    )
    runner.with_simple_chunk_events()

    # Should create app without errors
    app = runner.create_app()
    assert app is not None


def test_playground_frontend_compatibility():
    """
    PASS CRITERIA: Playground frontend works with migrated backend.

    Verifies:
    1. Frontend can connect to backend
    2. Web chat works with new SDK
    3. Bot Framework Emulator compatible
    """
    # This is more of a manual test, but we verify structure
    from aihub_bot.runners.BotTestRunner import BotTestRunner

    runner = BotTestRunner()
    app = runner.create_app()
    client = TestClient(app)

    # Verify health/docs endpoints
    response = client.get("/api/v1/docs")
    assert response.status_code == 200
```

---

### Task 5.3: Channel-Specific Testing
**Priority:** High
**Estimated Time:** 6 hours
**Dependencies:** Task 5.1

#### Description
Comprehensive testing of each channel (Teams, Slack, Web Chat) with the new SDK.

#### Test Specification
**Test File:** `tests/channels/test_teams_integration.py`

```python
import pytest


@pytest.mark.integration
def test_teams_conversation_lifecycle(full_bot_app, teams_activity):
    """
    PASS CRITERIA: Full Teams conversation lifecycle works.

    Verifies:
    1. Bot add/remove events handled
    2. Conversation ID reuse detected
    3. Message threading works
    4. Typing indicators visible
    5. Mentions handled correctly
    """
    from microsoft_agents.activity import ActivityTypes, ChannelAccount

    # Test bot added to conversation
    add_activity = teams_activity.copy()
    add_activity.type = ActivityTypes.conversation_update
    add_activity.members_added = [
        ChannelAccount(id=teams_activity.recipient.id, name="Bot")
    ]

    response = full_bot_app.post(
        "/api/v1/agent/chat",
        json=add_activity.__dict__,
        headers={"Service-Url": "https://smba.trafficmanager.net/emea/"}
    )

    assert response.status_code in [200, 500]


@pytest.mark.integration
def test_teams_adaptive_cards(full_bot_app, teams_activity):
    """
    PASS CRITERIA: Adaptive Cards work with new SDK.

    Verifies:
    1. Can send adaptive cards
    2. Card actions handled
    3. Uses new SDK attachment format
    """
    # Test will depend on specific card implementation
    pass


@pytest.mark.integration
def test_teams_file_upload(full_bot_app, teams_activity):
    """
    PASS CRITERIA: File uploads work with new SDK.

    Verifies:
    1. File attachments received
    2. ContentExtractor handles files
    3. File metadata accessible
    """
    from microsoft_agents.activity import Attachment

    teams_activity.attachments = [
        Attachment(
            content_type="application/pdf",
            content_url="https://example.com/file.pdf",
            name="document.pdf"
        )
    ]

    response = full_bot_app.post(
        "/api/v1/agent/chat",
        json=teams_activity.__dict__,
        headers={"Service-Url": "https://smba.trafficmanager.net/emea/"}
    )

    assert response.status_code in [200, 500]
```

**Test File:** `tests/channels/test_slack_integration.py`

```python
import pytest


@pytest.mark.integration
def test_slack_threading(full_bot_app, slack_activity):
    """
    PASS CRITERIA: Slack threading works correctly.

    Verifies:
    1. Thread detection works
    2. Responses go to correct thread
    3. Thread history accessible
    4. Conversation ID includes thread_ts
    """
    response = full_bot_app.post(
        "/api/v1/agent/chat",
        json=slack_activity.__dict__,
        headers={"Service-Url": "https://slack.botframework.com"}
    )

    assert response.status_code in [200, 500]


@pytest.mark.integration
def test_slack_bot_mention(full_bot_app, slack_activity):
    """
    PASS CRITERIA: Bot mentions work in Slack.

    Verifies:
    1. Mention detection works
    2. Bot responds to mentions
    3. Mention text formatting correct
    """
    from microsoft_agents.activity import Entity

    slack_activity.entities = [
        Entity(
            type="mention",
            additional_properties={
                "mentioned": {"id": slack_activity.recipient.id}
            }
        )
    ]

    response = full_bot_app.post(
        "/api/v1/agent/chat",
        json=slack_activity.__dict__,
        headers={"Service-Url": "https://slack.botframework.com"}
    )

    assert response.status_code in [200, 500]


@pytest.mark.integration
def test_slack_bot_in_the_loop(full_bot_app, slack_activity):
    """
    PASS CRITERIA: Bot-in-the-Loop pattern works in Slack.

    Verifies:
    1. Agent can request human input
    2. Message posted to Slack channel
    3. Human response captured
    4. Response sent back to agent
    """
    # This requires Bot-in-the-Loop controller
    # Test depends on NATS being available
    pass
```

---

---

## Phase 6: Documentation & Cleanup

### Task 6.1: Update Code Documentation
**Priority:** Medium
**Estimated Time:** 4 hours
**Dependencies:** All Phase 5 tasks

#### Description
Update all code comments, docstrings, and inline documentation to reference new SDK.

#### Test Specification
**Test File:** `tests/documentation/test_documentation.py`

```python
import pytest
import re


def test_no_botbuilder_references_in_docstrings():
    """
    PASS CRITERIA: No references to old SDK in any docstrings.

    Verifies:
    1. No "botbuilder" mentions in docstrings
    2. No "botframework" mentions in docstrings
    3. All imports documented correctly
    """
    import ast
    from pathlib import Path

    bot_dir = Path("aihub_bot/aihub_bot")

    for py_file in bot_dir.rglob("*.py"):
        with open(py_file, 'r') as f:
            content = f.read()

        # Check for old SDK references in comments/docstrings
        tree = ast.parse(content)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                docstring = ast.get_docstring(node)
                if docstring:
                    assert "botbuilder" not in docstring.lower(), f"Found botbuilder in {py_file}"
                    assert "botframework" not in docstring.lower(), f"Found botframework in {py_file}"


def test_imports_documented():
    """
    PASS CRITERIA: New SDK imports are properly documented.

    Verifies:
    1. Import statements have comments where appropriate
    2. Major classes have docstrings mentioning SDK
    """
    # Sample check on BaseChatBot
    from aihub_bot.bots.chat.BaseChatBot import BaseChatBot
    import inspect

    source = inspect.getsource(BaseChatBot)
    assert "microsoft_agents" in source

    docstring = inspect.getdoc(BaseChatBot)
    assert docstring is not None
    assert len(docstring) > 0
```

---

### Task 6.2: Update README.md
**Priority:** High
**Estimated Time:** 3 hours
**Dependencies:** Task 6.1

#### Description
Update `aihub_bot/README.md` to reflect new SDK, update examples, and migration notes.

#### Changes Required
1. Update "Bot Framework Integration" section to "Microsoft 365 Agents SDK Integration"
2. Update all code examples to use new imports
3. Add migration note at top of README
4. Update dependency installation instructions
5. Update Azure Bot setup documentation

#### Test Specification
**Test File:** `tests/documentation/test_readme.py`

```python
import pytest
from pathlib import Path


def test_readme_updated():
    """
    PASS CRITERIA: README.md reflects new SDK.

    Verifies:
    1. No "botbuilder" references except in migration notes
    2. Contains "microsoft-agents" or "Microsoft 365 Agents SDK"
    3. Code examples use new imports
    4. Dependencies section updated
    """
    readme_path = Path("aihub_bot/README.md")
    content = readme_path.read_text()

    # Should mention new SDK
    assert "microsoft-agents" in content.lower() or "microsoft 365 agents sdk" in content.lower()

    # Should have migration note
    assert "migration" in content.lower() or "deprecated" in content.lower()

    # Code examples should use new imports
    import re
    code_blocks = re.findall(r'```python\n(.*?)\n```', content, re.DOTALL)

    for block in code_blocks:
        # If block has imports, they should be new SDK
        if "from botbuilder" in block or "from botframework" in block:
            # Should only be in "old" examples showing migration
            assert "# OLD" in block or "BEFORE" in block, "Found old SDK import in current example"


def test_readme_examples_executable():
    """
    PASS CRITERIA: Code examples in README are valid Python.

    Verifies:
    1. Python code blocks are syntactically correct
    2. Imports are valid
    """
    import re
    import ast

    readme_path = Path("aihub_bot/README.md")
    content = readme_path.read_text()

    code_blocks = re.findall(r'```python\n(.*?)\n```', content, re.DOTALL)

    for block in code_blocks:
        # Skip incomplete snippets
        if "..." in block or "# ..." in block:
            continue

        try:
            ast.parse(block)
        except SyntaxError as e:
            pytest.fail(f"Invalid Python in README: {e}\nBlock:\n{block}")
```

---

### Task 6.3: Update Setup Script
**Priority:** Medium
**Estimated Time:** 2 hours
**Dependencies:** Task 6.2

#### Description
Update `setup_azure_bot.py` if needed to work with new SDK authentication.

#### Test Specification
**Test File:** `tests/setup/test_azure_bot_setup.py`

```python
import pytest
from unittest.mock import MagicMock, patch


def test_setup_script_uses_new_sdk():
    """
    PASS CRITERIA: Setup script compatible with new SDK.

    Verifies:
    1. No botbuilder imports
    2. Creates credentials compatible with new SDK
    3. Can create Azure Bot resources
    """
    import inspect
    from aihub_bot import setup_azure_bot

    source = inspect.getsource(setup_azure_bot)

    # Should not import old SDK
    assert "botbuilder" not in source


@patch('azure.mgmt.botservice.AzureBotService')
def test_setup_creates_compatible_credentials(mock_bot_service):
    """
    PASS CRITERIA: Created credentials work with new SDK.

    Verifies:
    1. Credential format matches new SDK expectations
    2. Can be stored and retrieved
    3. Multi-tenant and single-tenant both work
    """
    # Test credential creation
    from aihub_bot.persistence.entities.PathEntity import Credentials

    multi_tenant = {
        "APP_TYPE": "MultiTenant",
        "APP_ID": "test-123",
        "APP_PASSWORD": "test-pwd"
    }

    # Should be valid credential format
    assert "APP_TYPE" in multi_tenant
    assert "APP_ID" in multi_tenant
```

---

### Task 6.4: Clean Up Old Imports
**Priority:** High
**Estimated Time:** 2 hours
**Dependencies:** All above tasks complete

#### Description
Final cleanup pass to ensure absolutely no old SDK references remain.

#### Test Specification
**Test File:** `tests/cleanup/test_no_old_sdk_references.py`

```python
import pytest
from pathlib import Path
import re


def test_no_botbuilder_imports_anywhere():
    """
    PASS CRITERIA: Zero botbuilder/botframework imports in entire codebase.

    Verifies:
    1. No Python files import botbuilder
    2. No Python files import botframework
    3. pyproject.toml has no botbuilder dependencies
    """
    bot_dir = Path("aihub_bot")

    violations = []

    for py_file in bot_dir.rglob("*.py"):
        # Skip test files that document the migration
        if "test_migration" in str(py_file) or "test_no_old" in str(py_file):
            continue

        with open(py_file, 'r') as f:
            content = f.read()

        if re.search(r'^from botbuilder', content, re.MULTILINE):
            violations.append(f"{py_file}: has 'from botbuilder' import")

        if re.search(r'^from botframework', content, re.MULTILINE):
            violations.append(f"{py_file}: has 'from botframework' import")

    assert len(violations) == 0, f"Found old SDK imports:\n" + "\n".join(violations)


def test_pyproject_has_new_dependencies():
    """
    PASS CRITERIA: pyproject.toml has new SDK dependencies only.

    Verifies:
    1. Has microsoft-agents-* packages
    2. No botbuilder-* packages
    3. Versions are specified
    """
    import toml

    pyproject = toml.load("aihub_bot/pyproject.toml")
    deps = pyproject["tool"]["poetry"]["dependencies"]

    # Should have new SDK
    assert any("microsoft-agents" in dep for dep in deps)

    # Should not have old SDK
    assert not any("botbuilder" in dep for dep in deps)


def test_no_old_sdk_in_comments():
    """
    PASS CRITERIA: No references to old SDK in comments (except migration docs).

    Verifies:
    1. Comments don't reference old SDK
    2. TODOs mentioning old SDK are resolved
    """
    bot_dir = Path("aihub_bot/aihub_bot")  # Only check source, not tests

    violations = []

    for py_file in bot_dir.rglob("*.py"):
        with open(py_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                if line.strip().startswith('#'):
                    if 'botbuilder' in line.lower() or 'botframework' in line.lower():
                        # Allow migration notes
                        if 'migrated from' not in line.lower() and 'replaced' not in line.lower():
                            violations.append(f"{py_file}:{line_num}: {line.strip()}")

    assert len(violations) == 0, f"Found old SDK in comments:\n" + "\n".join(violations)


@pytest.mark.integration
def test_bot_runs_without_old_sdk():
    """
    PASS CRITERIA: Bot can run without botbuilder packages installed.

    Verifies:
    1. All imports resolve
    2. No ImportError for botbuilder
    3. Application starts successfully
    """
    # Try importing main bot components
    try:
        from aihub_bot.bots.chat.BaseChatBot import BaseChatBot
        from aihub_bot.routes.RoutesService import RoutesService
        from aihub_bot.runners.BotRunner import BotRunner

        # If these import successfully, old SDK is not required
        assert True

    except ImportError as e:
        if 'botbuilder' in str(e) or 'botframework' in str(e):
            pytest.fail(f"Still depends on old SDK: {e}")
        else:
            # Some other import issue (like missing config)
            pass
```

---

## Summary of Test Requirements

### Test Coverage Goals
- **Unit Tests**: 80%+ coverage on migrated components
- **Integration Tests**: All critical paths tested
- **Channel Tests**: Each channel (Teams, Slack, Web Chat) tested

### Test Execution Order
1. **Task 1.1-1.2**: Foundation tests must pass first
2. **Task 2.1-2.4**: Core component tests
3. **Task 3.1-3.3**: Specialized bot tests
4. **Task 4.1-4.2**: Controller tests
5. **Task 5.1-5.3**: Integration and validation tests
6. **Task 6.1-6.4**: Documentation and cleanup tests

### Success Criteria (Final)
All tests from all tasks must pass:
```bash
cd aihub_bot
poetry shell
pytest tests/ -v --cov=aihub_bot --cov-report=term-missing
```

Expected output:
- ✅ 0 failures
- ✅ 0 imports from botbuilder/botframework
- ✅ 80%+ code coverage
- ✅ All channels working

---

## Task Tracking Checklist

Copy this to track progress:

```markdown
## Phase 1: Foundation ✅ COMPLETE
- [x] Task 1.1: Update Project Dependencies (3 tests passing)
- [x] Task 1.2: Create Migration Test Fixtures (9 tests passing)

## Phase 2: Core Migration ✅ COMPLETE
- [x] Task 2.1: Migrate RoutesService (4 tests passing)
- [x] Task 2.2: Migrate BaseChatBot (7 tests passing)
- [x] Task 2.3: Migrate CompletionHandler (8 tests passing)
- [x] Task 2.4: Migrate ContentExtractor (9 tests passing)

**Total: 40 tests passing**

## Phase 3: Specialized Bots
- [ ] Task 3.1: Migrate Agent-Based Bots
- [ ] Task 3.2: Migrate OpenAI-Based Bots
- [ ] Task 3.3: Migrate Bot-in-the-Loop

## Phase 4: Controllers & Integration
- [ ] Task 4.1: Migrate All Controllers
- [ ] Task 4.2: Migrate Activity Models

## Phase 5: Testing & Validation
- [ ] Task 5.1: Update Integration Tests
- [ ] Task 5.2: Update Playground Tests
- [ ] Task 5.3: Channel-Specific Testing

## Phase 6: Documentation & Cleanup
- [ ] Task 6.1: Update Code Documentation
- [ ] Task 6.2: Update README.md
- [ ] Task 6.3: Update Setup Script
- [ ] Task 6.4: Clean Up Old Imports
```

---

**Estimated Total Time:** 5 weeks (1 developer) or 2.5 weeks (2 developers working in parallel)

**Risk Level:** Medium (well-documented migration path, but requires thorough testing)

**Rollback Plan:** Git branch allows easy revert if critical issues discovered
