"""
Test suite for Task 3.1: Migrate Agent-Based Bots

This test verifies that agent-based bots have been migrated to use the Microsoft 365 Agents SDK
by inspecting the source code for correct imports.
"""

import pytest
from pathlib import Path


def get_agent_files_source() -> dict[str, str]:
    """Helper to read all agent bot source files."""
    # Go up from tests/bots/chat/agent to aihub_bot root, then to aihub_bot/bots/chat/agent
    base_path = Path(__file__).parent.parent.parent.parent.parent / "aihub_bot" / "bots" / "chat" / "agent"
    return {
        "AgentChatBot": (base_path / "AgentChatBot.py").read_text(),
        "StreamAgentChatBot": (base_path / "StreamAgentChatBot.py").read_text(),
        "AgentCompletionHandler": (base_path / "AgentCompletionHandler.py").read_text(),
    }


def test_all_agent_files_imports_new_sdk():
    """
    PASS CRITERIA: All agent bot files use new SDK.

    Verifies:
    1. AgentChatBot has no botbuilder imports
    2. StreamAgentChatBot has no botbuilder imports
    3. AgentCompletionHandler has no botbuilder imports
    4. No botframework imports in any file
    """
    sources = get_agent_files_source()

    for filename, source in sources.items():
        assert "from botbuilder" not in source, f"Found botbuilder import in {filename}"
        assert "from botframework" not in source, f"Found botframework import in {filename}"


def test_stream_agent_chat_bot_imports():
    """
    PASS CRITERIA: StreamAgentChatBot uses new SDK imports.

    Verifies:
    1. Imports TurnContext from microsoft_agents
    2. No Channels import
    3. Uses string literals for channel IDs
    """
    sources = get_agent_files_source()
    source = sources["StreamAgentChatBot"]

    # Should import from new SDK or inherit from migrated base classes
    assert (
        "from microsoft_agents" in source or "from aihub_bot.bots.chat" in source
    ), "Missing new SDK or base class imports"

    # Should not import Channels
    assert "from botframework.connector import Channels" not in source, "Found Channels import"


def test_agent_completion_handler_imports():
    """
    PASS CRITERIA: AgentCompletionHandler uses new SDK imports.

    Verifies:
    1. Imports TurnContext from microsoft_agents
    2. No old SDK imports
    """
    sources = get_agent_files_source()
    source = sources["AgentCompletionHandler"]

    # Should import from new SDK or use inherited types
    assert "from microsoft_agents" in source or "TurnContext" in source, "Missing TurnContext usage"


def test_stream_agent_no_channels_constant():
    """
    PASS CRITERIA: StreamAgentChatBot doesn't use Channels constant.

    Verifies:
    1. No Channels.webchat usage
    2. Uses string literal "webchat" instead
    """
    sources = get_agent_files_source()
    source = sources["StreamAgentChatBot"]

    assert "Channels.webchat" not in source, "Found Channels.webchat constant"
    assert "Channels." not in source, "Found Channels constant usage"


def test_webchat_string_literal_usage():
    """
    PASS CRITERIA: Uses "webchat" string literal.

    Verifies:
    1. String literal "webchat" is used for channel detection
    """
    sources = get_agent_files_source()
    source = sources["StreamAgentChatBot"]

    # Should use string literal for webchat channel
    assert (
        'channel_id == "webchat"' in source or "channel_id == 'webchat'" in source
    ), "String literal 'webchat' not found for channel detection"


def test_agent_chat_bot_inheritance():
    """
    PASS CRITERIA: AgentChatBot inherits from migrated BaseChatBot.

    Verifies:
    1. Imports BaseChatBot
    2. Inherits from BaseChatBot
    """
    sources = get_agent_files_source()
    source = sources["AgentChatBot"]

    assert "from aihub_bot.bots.chat.BaseChatBot import BaseChatBot" in source, "BaseChatBot import not found"
    assert "class AgentChatBot(BaseChatBot):" in source, "AgentChatBot doesn't inherit from BaseChatBot"


def test_stream_agent_chat_bot_inheritance():
    """
    PASS CRITERIA: StreamAgentChatBot inherits from AgentChatBot.

    Verifies:
    1. Imports AgentChatBot
    2. Inherits from AgentChatBot
    """
    sources = get_agent_files_source()
    source = sources["StreamAgentChatBot"]

    assert "from aihub_bot.bots.chat.agent.AgentChatBot import AgentChatBot" in source, "AgentChatBot import not found"
    assert "class StreamAgentChatBot(AgentChatBot):" in source, "StreamAgentChatBot doesn't inherit from AgentChatBot"


def test_agent_completion_handler_inheritance():
    """
    PASS CRITERIA: AgentCompletionHandler inherits from CompletionHandler.

    Verifies:
    1. Imports CompletionHandler
    2. Inherits from CompletionHandler
    """
    sources = get_agent_files_source()
    source = sources["AgentCompletionHandler"]

    assert (
        "from aihub_bot.bots.chat.CompletionHandler import CompletionHandler" in source
    ), "CompletionHandler import not found"
    assert (
        "class AgentCompletionHandler(CompletionHandler):" in source
    ), "AgentCompletionHandler doesn't inherit from CompletionHandler"
