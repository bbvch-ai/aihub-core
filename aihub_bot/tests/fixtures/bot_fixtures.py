"""Shared fixtures for bot migration testing."""

from datetime import UTC
from unittest.mock import AsyncMock, MagicMock

import pytest
from microsoft_agents.activity import Activity, ActivityTypes, ChannelAccount, ConversationAccount
from microsoft_agents.hosting.core import TurnContext


@pytest.fixture
def mock_activity() -> Activity:
    """
    Create a mock Activity for testing.

    Returns a basic message activity with all required fields populated.
    """
    from datetime import datetime

    return Activity(
        type=ActivityTypes.message,
        id="test-activity-123",
        text="Hello, bot!",
        from_property=ChannelAccount(id="user-123", name="Test User"),
        recipient=ChannelAccount(id="bot-456", name="Test Bot"),
        conversation=ConversationAccount(id="conv-789", name="Test Conversation"),
        channel_id="msteams",
        locale="en-US",
        timestamp=datetime.now(UTC),
        service_url="https://test.botframework.com",
    )


@pytest.fixture
def mock_turn_context(mock_activity: Activity) -> TurnContext:
    """
    Create a mock TurnContext for testing.

    The TurnContext is mocked to avoid needing a real adapter.
    send_activity and update_activity are AsyncMock to simulate async behavior.
    """
    context = MagicMock(spec=TurnContext)
    context.activity = mock_activity
    context.send_activity = AsyncMock(return_value=MagicMock(id="response-123"))
    context.update_activity = AsyncMock()
    context.delete_activity = AsyncMock()

    return context


@pytest.fixture
def teams_activity(mock_activity: Activity) -> Activity:
    """
    Create a Teams-specific activity.

    Sets channel_id to "msteams" and includes Teams-specific properties.
    """
    activity = mock_activity
    activity.channel_id = "msteams"
    activity.service_url = "https://smba.trafficmanager.net/emea/"
    return activity


@pytest.fixture
def slack_activity(mock_activity: Activity) -> Activity:
    """
    Create a Slack-specific activity.

    Sets channel_id to "slack" and includes Slack-specific conversation ID format
    and channel_data structure.
    """
    activity = mock_activity
    activity.channel_id = "slack"
    activity.conversation = ConversationAccount(
        id="B12345:T67890:C11111",  # Slack channel conversation ID format
        name="Test Slack Channel",
    )
    activity.service_url = "https://slack.botframework.com"

    # Add Slack-specific channel_data
    activity.channel_data = {
        "SlackMessage": {"event": {"ts": "1234567890.123456", "thread_ts": "1234567890.123456"}},
        "team": {"id": "T67890"},
        "channel": {"id": "C11111"},
    }

    return activity


@pytest.fixture
def webchat_activity(mock_activity: Activity) -> Activity:
    """
    Create a Web Chat-specific activity.

    Sets channel_id to "webchat" for testing web chat scenarios.
    """
    activity = mock_activity
    activity.channel_id = "webchat"
    activity.service_url = "https://webchat.botframework.com"
    return activity
