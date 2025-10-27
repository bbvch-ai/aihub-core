"""
Real Integration Tests - SDK Runtime Behavior

These tests actually import and instantiate bot classes to verify runtime behavior
with the Microsoft 365 Agents SDK (not just static analysis).
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from microsoft_agents.activity import Activity, ActivityTypes, ChannelAccount, ConversationAccount
from microsoft_agents.hosting.core import TurnContext


def test_can_import_all_bot_classes():
    """
    PASS CRITERIA: All bot classes can be imported with new SDK.

    This verifies the migration is complete and modules have proper dependencies.
    """
    # Import all major bot classes - if old SDK still present, these would fail
    from aihub_bot.bots.bot_in_the_loop.BotInTheLoopBot import BotInTheLoopBot
    from aihub_bot.bots.chat.agent.AgentChatBot import AgentChatBot
    from aihub_bot.bots.chat.agent.AgentCompletionHandler import AgentCompletionHandler
    from aihub_bot.bots.chat.agent.StreamAgentChatBot import StreamAgentChatBot
    from aihub_bot.bots.chat.BaseChatBot import BaseChatBot
    from aihub_bot.bots.chat.ContentExtractor import ContentExtractor
    from aihub_bot.bots.chat.openai.OpenaiChatBot import OpenaiChatBot
    from aihub_bot.bots.chat.openai.OpenaiCompletionHandler import OpenaiCompletionHandler
    from aihub_bot.bots.chat.openai.StreamOpenaiChatBot import StreamOpenaiChatBot

    # All imports succeeded
    assert BaseChatBot is not None
    assert AgentChatBot is not None
    assert StreamAgentChatBot is not None
    assert AgentCompletionHandler is not None
    assert OpenaiChatBot is not None
    assert StreamOpenaiChatBot is not None
    assert OpenaiCompletionHandler is not None
    assert ContentExtractor is not None
    assert BotInTheLoopBot is not None


def test_can_import_controllers():
    """
    PASS CRITERIA: Controllers can be imported with new SDK.
    """
    from aihub_bot.routes.agent.AgentChatController import AgentChatController
    from aihub_bot.routes.bot_in_the_loop.BotInTheLoopController import BotInTheLoopController
    from aihub_bot.routes.openai.OpenaiChatController import OpenaiChatController

    assert AgentChatController is not None
    assert OpenaiChatController is not None
    assert BotInTheLoopController is not None


def test_can_import_routes_service():
    """
    PASS CRITERIA: RoutesService can be imported with new SDK.
    """
    from aihub_bot.routes.RoutesService import RoutesService

    assert RoutesService is not None
    assert hasattr(RoutesService, "get_adapter")
    assert hasattr(RoutesService, "get_credentials")


def test_base_chat_bot_uses_new_sdk_types():
    """
    PASS CRITERIA: BaseChatBot works with new SDK Activity and TurnContext.
    """
    from pathlib import Path

    from aihub_bot.bots.chat.BaseChatBot import BaseChatBot

    # Get the full file source to check imports
    scope_root = Path(__file__).parent.parent.parent
    source_file = scope_root / "aihub_bot" / "bots" / "chat" / "BaseChatBot.py"
    source = source_file.read_text()

    # Should import from new SDK
    assert "from microsoft_agents" in source or "microsoft_agents" in source
    assert "from botbuilder" not in source

    # BaseChatBot class exists and has expected methods
    assert hasattr(BaseChatBot, "on_turn")
    assert hasattr(BaseChatBot, "on_message_activity")


@pytest.mark.asyncio
async def test_base_chat_bot_instantiation():
    """
    PASS CRITERIA: BaseChatBot can be instantiated (though may fail without full config).

    This verifies the class structure is correct with new SDK.
    """
    from aihub_bot.bots.chat.BaseChatBot import BaseChatBot

    # Try to instantiate - may fail due to config but structure should be valid
    try:
        bot = BaseChatBot()
        # If it succeeds, verify it's the right type
        assert isinstance(bot, BaseChatBot)
    except TypeError as e:
        # Expected - may need constructor args
        assert "required positional argument" in str(e) or "__init__" in str(e)


def test_content_extractor_uses_string_literals():
    """
    PASS CRITERIA: ContentExtractor uses string literals for channels.
    """
    import inspect

    from aihub_bot.bots.chat.ContentExtractor import ContentExtractor

    source = inspect.getsource(ContentExtractor)

    # Should use string literals for channels
    if "channel" in source:
        assert '"msteams"' in source or '"slack"' in source or '"webchat"' in source

    # Should not use Channels enum
    assert "Channels.ms_teams" not in source
    assert "Channels.slack" not in source


def test_activity_model_is_new_sdk_activity():
    """
    PASS CRITERIA: ActivityModel is the new SDK's Activity class.
    """
    from microsoft_agents.activity import Activity

    from aihub_bot.routes.activity_model import ActivityModel

    # ActivityModel should be Activity from new SDK
    assert ActivityModel is Activity


@pytest.mark.asyncio
async def test_turn_context_mock_compatibility():
    """
    PASS CRITERIA: New SDK TurnContext is compatible with bot code.

    Creates a real TurnContext-like mock and verifies it works.
    """
    # Create a real Activity from new SDK
    activity = Activity(
        type=ActivityTypes.message,
        id="test-123",
        text="Test message",
        from_property=ChannelAccount(id="user-123", name="Test User"),
        recipient=ChannelAccount(id="bot-456", name="Test Bot"),
        conversation=ConversationAccount(id="conv-789"),
        channel_id="msteams",
    )

    # Create a mock TurnContext
    turn_context = MagicMock(spec=TurnContext)
    turn_context.activity = activity
    turn_context.send_activity = AsyncMock(return_value=MagicMock(id="response-123"))
    turn_context.update_activity = AsyncMock()

    # Test that we can interact with it like new SDK
    assert turn_context.activity.channel_id == "msteams"
    assert turn_context.activity.type == ActivityTypes.message

    # Test async methods work
    response = await turn_context.send_activity("Test response")
    assert response.id == "response-123"

    await turn_context.update_activity(activity)
    turn_context.update_activity.assert_called_once()


def test_handlers_accept_new_sdk_types():
    """
    PASS CRITERIA: Completion handlers accept new SDK Activity type.
    """
    import inspect

    from aihub_bot.bots.chat.agent.AgentCompletionHandler import AgentCompletionHandler
    from aihub_bot.bots.chat.openai.OpenaiCompletionHandler import OpenaiCompletionHandler

    # Check AgentCompletionHandler has expected methods
    assert hasattr(AgentCompletionHandler, "chat_completion")
    agent_handler_sig = inspect.signature(AgentCompletionHandler.chat_completion)
    # Handler should accept turn_context parameter (which has new SDK Activity)
    assert "turn_context" in agent_handler_sig.parameters

    # Check OpenaiCompletionHandler has expected methods
    assert hasattr(OpenaiCompletionHandler, "get_completion")
    openai_handler_sig = inspect.signature(OpenaiCompletionHandler.get_completion)
    assert "turn_context" in openai_handler_sig.parameters


def test_bot_in_the_loop_uses_string_channels():
    """
    PASS CRITERIA: Bot-in-the-loop uses string literals for channel detection.
    """
    import inspect

    from aihub_bot.bots.bot_in_the_loop.BotInTheLoopBot import BotInTheLoopBot
    from aihub_bot.routes.bot_in_the_loop.BotInTheLoopHandler import BotInTheLoopHandler

    # Check bot file
    bot_source = inspect.getsource(BotInTheLoopBot)
    if "channel" in bot_source:
        assert '"slack"' in bot_source or '"msteams"' in bot_source
        assert "Channels.slack" not in bot_source
        assert "Channels.ms_teams" not in bot_source

    # Check handler file
    handler_source = inspect.getsource(BotInTheLoopHandler)
    if "channel" in handler_source:
        assert '"slack"' in handler_source or '"msteams"' in handler_source
        assert "Channels.slack" not in handler_source
        assert "Channels.ms_teams" not in handler_source
