"""
Test suite for Task 3.2: Migrate OpenAI-Based Bots

This test verifies that OpenAI-based bots have been migrated to use the Microsoft 365 Agents SDK
by inspecting the source code for correct imports.
"""

import pytest
from pathlib import Path


def get_openai_files_source() -> dict[str, str]:
    """Helper to read all OpenAI bot source files."""
    # Go up from tests/bots/chat/openai to aihub_bot root, then to aihub_bot/bots/chat/openai
    base_path = Path(__file__).parent.parent.parent.parent.parent / "aihub_bot" / "bots" / "chat" / "openai"
    return {
        "OpenaiChatBot": (base_path / "OpenaiChatBot.py").read_text(),
        "StreamOpenaiChatBot": (base_path / "StreamOpenaiChatBot.py").read_text(),
        "OpenaiCompletionHandler": (base_path / "OpenaiCompletionHandler.py").read_text(),
    }


def test_all_openai_files_imports_new_sdk():
    """
    PASS CRITERIA: All OpenAI bot files use new SDK.

    Verifies:
    1. OpenaiChatBot has no botbuilder imports
    2. StreamOpenaiChatBot has no botbuilder imports
    3. OpenaiCompletionHandler has no botbuilder imports
    4. No botframework imports in any file
    """
    sources = get_openai_files_source()

    for filename, source in sources.items():
        assert "from botbuilder" not in source, f"Found botbuilder import in {filename}"
        assert "from botframework" not in source, f"Found botframework import in {filename}"


def test_stream_openai_chat_bot_imports():
    """
    PASS CRITERIA: StreamOpenaiChatBot uses new SDK imports.

    Verifies:
    1. Imports TurnContext from microsoft_agents
    2. No Channels import
    3. Uses string literals for channel IDs
    """
    sources = get_openai_files_source()
    source = sources["StreamOpenaiChatBot"]

    # Should import from new SDK or inherit from migrated base classes
    assert (
        "from microsoft_agents" in source or "from aihub_bot.bots.chat" in source
    ), "Missing new SDK or base class imports"

    # Should not import Channels
    assert "from botframework.connector import Channels" not in source, "Found Channels import"


def test_openai_completion_handler_imports():
    """
    PASS CRITERIA: OpenaiCompletionHandler uses new SDK imports.

    Verifies:
    1. Imports TurnContext from microsoft_agents
    2. No old SDK imports
    """
    sources = get_openai_files_source()
    source = sources["OpenaiCompletionHandler"]

    # Should import from new SDK
    assert "from microsoft_agents" in source, "Missing microsoft_agents import"


def test_stream_openai_no_channels_constant():
    """
    PASS CRITERIA: StreamOpenaiChatBot doesn't use Channels constant.

    Verifies:
    1. No Channels.webchat usage
    2. Uses string literal "webchat" instead
    """
    sources = get_openai_files_source()
    source = sources["StreamOpenaiChatBot"]

    assert "Channels.webchat" not in source, "Found Channels.webchat constant"
    assert "Channels." not in source, "Found Channels constant usage"


def test_openai_completion_no_channels_constant():
    """
    PASS CRITERIA: OpenaiCompletionHandler doesn't use Channels constant.

    Verifies:
    1. No Channels.ms_teams usage
    2. Uses string literal "msteams" instead
    """
    sources = get_openai_files_source()
    source = sources["OpenaiCompletionHandler"]

    assert "Channels.ms_teams" not in source, "Found Channels.ms_teams constant"
    assert (
        'channel_id == "msteams"' in source or "channel_id == 'msteams'" in source
    ), "String literal 'msteams' not found"


def test_webchat_string_literal_usage():
    """
    PASS CRITERIA: Uses "webchat" string literal.

    Verifies:
    1. String literal "webchat" is used for channel detection
    """
    sources = get_openai_files_source()
    source = sources["StreamOpenaiChatBot"]

    # Should use string literal for webchat channel
    assert (
        'channel_id == "webchat"' in source or "channel_id == 'webchat'" in source
    ), "String literal 'webchat' not found for channel detection"


def test_openai_chat_bot_inheritance():
    """
    PASS CRITERIA: OpenaiChatBot inherits from migrated BaseChatBot.

    Verifies:
    1. Imports BaseChatBot
    2. Inherits from BaseChatBot
    """
    sources = get_openai_files_source()
    source = sources["OpenaiChatBot"]

    assert "from aihub_bot.bots.chat.BaseChatBot import BaseChatBot" in source, "BaseChatBot import not found"
    assert "class OpenaiChatBot(BaseChatBot):" in source, "OpenaiChatBot doesn't inherit from BaseChatBot"


def test_stream_openai_chat_bot_inheritance():
    """
    PASS CRITERIA: StreamOpenaiChatBot inherits from OpenaiChatBot.

    Verifies:
    1. Imports OpenaiChatBot
    2. Inherits from OpenaiChatBot
    """
    sources = get_openai_files_source()
    source = sources["StreamOpenaiChatBot"]

    assert (
        "from aihub_bot.bots.chat.openai.OpenaiChatBot import OpenaiChatBot" in source
    ), "OpenaiChatBot import not found"
    assert (
        "class StreamOpenaiChatBot(OpenaiChatBot):" in source
    ), "StreamOpenaiChatBot doesn't inherit from OpenaiChatBot"


def test_openai_completion_handler_inheritance():
    """
    PASS CRITERIA: OpenaiCompletionHandler inherits from CompletionHandler.

    Verifies:
    1. Imports CompletionHandler
    2. Inherits from CompletionHandler
    """
    sources = get_openai_files_source()
    source = sources["OpenaiCompletionHandler"]

    assert (
        "from aihub_bot.bots.chat.CompletionHandler import CompletionHandler" in source
    ), "CompletionHandler import not found"
    assert (
        "class OpenaiCompletionHandler(CompletionHandler):" in source
    ), "OpenaiCompletionHandler doesn't inherit from CompletionHandler"


def test_no_teams_info_import():
    """
    PASS CRITERIA: No TeamsInfo import from old SDK.

    Verifies:
    1. No botbuilder.core.teams.TeamsInfo import
    2. Uses alternative approach or new SDK equivalent
    """
    sources = get_openai_files_source()
    source = sources["OpenaiCompletionHandler"]

    assert "from botbuilder.core.teams import TeamsInfo" not in source, "Found TeamsInfo import from old SDK"


def test_no_teams_channel_account_import():
    """
    PASS CRITERIA: No TeamsChannelAccount import from old SDK.

    Verifies:
    1. No botbuilder.schema.teams.TeamsChannelAccount import
    2. Uses alternative approach or new SDK equivalent
    """
    sources = get_openai_files_source()
    source = sources["OpenaiCompletionHandler"]

    assert (
        "from botbuilder.schema.teams import TeamsChannelAccount" not in source
    ), "Found TeamsChannelAccount import from old SDK"
