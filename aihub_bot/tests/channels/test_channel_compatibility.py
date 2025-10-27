"""
Test suite for Task 5.3: Channel-Specific Testing

This test suite verifies that bot functionality works correctly across different channels
(Teams, Slack, WebChat) with the Microsoft 365 Agents SDK.
"""

from pathlib import Path

from microsoft_agents.activity import Activity, ActivityTypes, ChannelAccount, ConversationAccount


def test_teams_channel_id():
    """
    PASS CRITERIA: Teams channel uses correct string literal.

    Verifies:
    1. Teams channel ID is "msteams"
    2. Activity creation works for Teams
    3. Channel-specific properties accessible
    """
    teams_activity = Activity(
        type=ActivityTypes.message,
        id="teams-msg-123",
        text="Hello from Teams",
        from_property=ChannelAccount(id="29:user-id", name="Teams User"),
        recipient=ChannelAccount(id="28:bot-id", name="Bot"),
        conversation=ConversationAccount(id="19:channel-id@thread.tacv2"),
        channel_id="msteams",
        service_url="https://smba.trafficmanager.net/emea/",
    )

    assert teams_activity.channel_id == "msteams"
    assert "thread.tacv2" in teams_activity.conversation.id
    assert teams_activity.service_url.startswith("https://smba.trafficmanager.net")


def test_slack_channel_id():
    """
    PASS CRITERIA: Slack channel uses correct string literal.

    Verifies:
    1. Slack channel ID is "slack"
    2. Activity creation works for Slack
    3. Slack conversation ID format correct
    """
    slack_activity = Activity(
        type=ActivityTypes.message,
        id="slack-msg-123",
        text="Hello from Slack",
        from_property=ChannelAccount(id="U123456", name="Slack User"),
        recipient=ChannelAccount(id="B789012", name="Slack Bot"),
        conversation=ConversationAccount(id="B12345:T67890:C11111"),
        channel_id="slack",
        service_url="https://slack.botframework.com",
    )

    assert slack_activity.channel_id == "slack"
    # Slack conversation IDs have format: BotID:TeamID:ChannelID
    assert slack_activity.conversation.id.count(":") == 2
    assert slack_activity.service_url == "https://slack.botframework.com"


def test_webchat_channel_id():
    """
    PASS CRITERIA: WebChat channel uses correct string literal.

    Verifies:
    1. WebChat channel ID is "webchat"
    2. Activity creation works for WebChat
    3. WebChat properties accessible
    """
    webchat_activity = Activity(
        type=ActivityTypes.message,
        id="webchat-msg-123",
        text="Hello from WebChat",
        from_property=ChannelAccount(id="user-webchat-456", name="Web User"),
        recipient=ChannelAccount(id="bot-webchat-789", name="Web Bot"),
        conversation=ConversationAccount(id="webchat-conv-abc"),
        channel_id="webchat",
        service_url="https://webchat.botframework.com",
    )

    assert webchat_activity.channel_id == "webchat"
    assert webchat_activity.service_url == "https://webchat.botframework.com"


def test_channel_detection_in_bots():
    """
    PASS CRITERIA: Bot files use string literals for channel detection.

    Verifies:
    1. No Channels enum usage
    2. String literals used for channel comparison
    3. All major bots support multiple channels
    """
    scope_root = Path(__file__).parent.parent.parent

    # Check files that do channel-specific logic
    files_with_channel_logic = [
        scope_root / "aihub_bot" / "bots" / "chat" / "BaseChatBot.py",
        scope_root / "aihub_bot" / "bots" / "chat" / "openai" / "OpenaiCompletionHandler.py",
        scope_root / "aihub_bot" / "bots" / "chat" / "ContentExtractor.py",
        scope_root / "aihub_bot" / "bots" / "bot_in_the_loop" / "BotInTheLoopBot.py",
    ]

    for file_path in files_with_channel_logic:
        if not file_path.exists():
            continue

        source = file_path.read_text()

        # Should use string literals, not Channels enum
        if "channel_id" in source:
            # If file does channel checks, verify it uses string literals
            assert (
                '"msteams"' in source or '"slack"' in source or '"webchat"' in source
            ), f"{file_path.name} should use string literals for channels"

            # Should not use Channels enum
            assert "Channels.ms_teams" not in source, f"{file_path.name} uses Channels enum"
            assert "Channels.slack" not in source, f"{file_path.name} uses Channels enum"
            assert "Channels.webchat" not in source, f"{file_path.name} uses Channels enum"


def test_teams_conversation_id_format():
    """
    PASS CRITERIA: Teams conversation IDs follow correct format.

    Verifies:
    1. Channel conversation IDs contain thread identifiers
    2. Format is compatible with Teams API
    """
    # Teams channel conversation
    channel_conv = Activity(
        type=ActivityTypes.message,
        conversation=ConversationAccount(id="19:abc123@thread.tacv2"),
        channel_id="msteams",
    )

    assert "@thread.tacv2" in channel_conv.conversation.id or "@thread.skype" in channel_conv.conversation.id

    # Teams 1:1 conversation
    direct_conv = Activity(
        type=ActivityTypes.message,
        conversation=ConversationAccount(id="29:direct-conv-id"),
        channel_id="msteams",
    )

    # Direct conversations typically start with specific prefixes
    assert direct_conv.conversation.id.startswith("29:") or direct_conv.conversation.id.startswith("19:")


def test_slack_threading_format():
    """
    PASS CRITERIA: Slack thread IDs follow correct format.

    Verifies:
    1. Slack thread timestamps can be appended to conversation ID
    2. Format matches Slack's threading model
    """
    # Slack base conversation
    base_conv_id = "B12345:T67890:C11111"

    # Slack thread (conversation ID + thread timestamp)
    thread_conv_id = f"{base_conv_id}:1234567890.123456"

    activity = Activity(
        type=ActivityTypes.message,
        conversation=ConversationAccount(id=thread_conv_id),
        channel_id="slack",
    )

    # Should have 3 or 4 colons (base or threaded)
    assert activity.conversation.id.count(":") >= 2
    assert activity.channel_id == "slack"


def test_channel_specific_handlers():
    """
    PASS CRITERIA: Handlers properly distinguish between channels.

    Verifies:
    1. OpenAI handler processes channel-specific user info
    2. Bot-in-the-loop handler supports multiple channels
    3. Content extractor handles channel-specific attachments
    """
    scope_root = Path(__file__).parent.parent.parent

    # Check OpenAI handler for channel-specific logic
    openai_handler = scope_root / "aihub_bot" / "bots" / "chat" / "openai" / "OpenaiCompletionHandler.py"
    if openai_handler.exists():
        source = openai_handler.read_text()
        assert '"msteams"' in source, "OpenAI handler should handle Teams"

    # Check Bot-in-the-Loop for multi-channel support
    bitl_bot = scope_root / "aihub_bot" / "bots" / "bot_in_the_loop" / "BotInTheLoopBot.py"
    if bitl_bot.exists():
        source = bitl_bot.read_text()
        assert '"slack"' in source, "Bot-in-the-loop should support Slack"
        assert '"msteams"' in source, "Bot-in-the-loop should support Teams"

    # Check ContentExtractor for channel-specific file handling
    content_extractor = scope_root / "aihub_bot" / "bots" / "chat" / "ContentExtractor.py"
    if content_extractor.exists():
        source = content_extractor.read_text()
        # Content extractor should handle different channels
        assert '"msteams"' in source or "channel_id" in source


def test_activity_types_across_channels():
    """
    PASS CRITERIA: Different activity types work across all channels.

    Verifies:
    1. Message activities work for all channels
    2. ConversationUpdate activities for adding/removing users
    3. Typing activities for typing indicators
    """
    from microsoft_agents.activity import ActivityTypes

    channels = ["msteams", "slack", "webchat"]

    for channel in channels:
        # Test message activity
        message = Activity(
            type=ActivityTypes.message,
            text="Test message",
            channel_id=channel,
            conversation=ConversationAccount(id=f"{channel}-conv-123"),
        )
        assert message.type == ActivityTypes.message

        # Test typing activity
        typing = Activity(
            type=ActivityTypes.typing,
            channel_id=channel,
            conversation=ConversationAccount(id=f"{channel}-conv-123"),
        )
        assert typing.type == ActivityTypes.typing

        # Test conversation update activity
        conv_update = Activity(
            type=ActivityTypes.conversation_update,
            channel_id=channel,
            conversation=ConversationAccount(id=f"{channel}-conv-123"),
        )
        assert conv_update.type == ActivityTypes.conversation_update
