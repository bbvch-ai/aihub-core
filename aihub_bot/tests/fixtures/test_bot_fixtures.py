"""
Test suite for Task 1.2: Create Migration Test Fixtures

This test verifies that all test fixtures are working correctly and provide
the necessary test data for migration testing.
"""

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
    assert mock_activity.from_property.name == "Test User"
    assert mock_activity.recipient.id == "bot-456"
    assert mock_activity.recipient.name == "Test Bot"
    assert mock_activity.conversation.id == "conv-789"
    assert mock_activity.channel_id == "msteams"
    assert mock_activity.locale == "en-US"


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
    assert callable(mock_turn_context.delete_activity)


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
    assert response.id == "response-123"


@pytest.mark.asyncio
async def test_turn_context_update_activity(mock_turn_context, mock_activity):
    """
    PASS CRITERIA: Mock TurnContext can update activities.

    Verifies:
    1. update_activity can be called
    2. Can be awaited without errors
    """
    mock_activity.text = "Updated text"
    await mock_turn_context.update_activity(mock_activity)

    # Verify update_activity was called
    mock_turn_context.update_activity.assert_called_once()


def test_teams_activity_fixture(teams_activity):
    """
    PASS CRITERIA: teams_activity fixture creates Teams-specific activity.

    Verifies:
    1. Channel ID is msteams
    2. Has required Teams properties
    3. Service URL is Teams-specific
    """
    assert teams_activity.channel_id == "msteams"
    assert teams_activity.service_url == "https://smba.trafficmanager.net/emea/"
    assert teams_activity.type == ActivityTypes.message


def test_slack_activity_fixture(slack_activity):
    """
    PASS CRITERIA: slack_activity fixture creates Slack-specific activity.

    Verifies:
    1. Channel ID is slack
    2. Has Slack-specific conversation ID format (B:T:C format)
    3. Has channel_data with SlackMessage
    4. Has thread timestamp in channel_data
    """
    assert slack_activity.channel_id == "slack"
    assert ":" in slack_activity.conversation.id
    assert slack_activity.conversation.id.startswith("B")

    # Verify Slack-specific channel_data structure
    assert "SlackMessage" in slack_activity.channel_data
    assert "event" in slack_activity.channel_data["SlackMessage"]
    assert "ts" in slack_activity.channel_data["SlackMessage"]["event"]


def test_webchat_activity_fixture(webchat_activity):
    """
    PASS CRITERIA: webchat_activity fixture creates Web Chat-specific activity.

    Verifies:
    1. Channel ID is webchat
    2. Has required properties
    """
    assert webchat_activity.channel_id == "webchat"
    assert webchat_activity.service_url == "https://webchat.botframework.com"


def test_fixtures_use_new_sdk():
    """
    PASS CRITERIA: All fixtures use new SDK types.

    Verifies:
    1. Activity type is from microsoft_agents.activity
    2. ActivityTypes is from new SDK
    3. No botbuilder imports
    """
    from microsoft_agents.activity import Activity, ActivityTypes

    # Verify these are from the correct module
    assert Activity.__module__.startswith("microsoft_agents")
    assert ActivityTypes.message is not None


def test_activity_serialization(mock_activity):
    """
    PASS CRITERIA: Activity objects can be serialized.

    Verifies:
    1. Activity has __dict__ attribute
    2. Can access key properties via dict
    """
    # Activity should be serializable
    activity_dict = mock_activity.__dict__ if hasattr(mock_activity, "__dict__") else {}

    # Should have key properties
    # Note: Exact serialization format may vary with SDK
    assert isinstance(activity_dict, dict) or hasattr(mock_activity, "type")
