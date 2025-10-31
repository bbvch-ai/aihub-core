"""
Test suite for Task 2.2: Migrate BaseChatBot

This test verifies that BaseChatBot has been migrated to use the Microsoft 365 Agents SDK
by inspecting the source code for correct imports and channel ID usage.
"""

from pathlib import Path


def get_base_chat_bot_source() -> str:
    """Helper to read BaseChatBot source file."""
    base_chat_bot_path = Path(__file__).parent.parent.parent.parent / "aihub_bot" / "bots" / "chat" / "BaseChatBot.py"
    return base_chat_bot_path.read_text()


def test_base_chat_bot_imports_new_sdk():
    """
    PASS CRITERIA: BaseChatBot uses new SDK imports only.

    Verifies:
    1. No botbuilder imports in source
    2. Uses microsoft_agents imports
    3. No botframework imports
    """
    source = get_base_chat_bot_source()

    assert "from botbuilder" not in source, "Found botbuilder import in BaseChatBot"
    assert "from botframework" not in source, "Found botframework import in BaseChatBot"
    assert "from microsoft_agents" in source, "microsoft_agents import not found"


def test_imports_activity_handler_from_new_sdk():
    """
    PASS CRITERIA: ActivityHandler is imported from microsoft_agents.

    Verifies:
    1. Imports from microsoft_agents.hosting.core
    2. ActivityHandler is the base class
    """
    source = get_base_chat_bot_source()

    assert "from microsoft_agents.hosting.core import ActivityHandler" in source, "ActivityHandler import not found"
    assert "class BaseChatBot(ActivityHandler):" in source, "BaseChatBot doesn't inherit from ActivityHandler"


def test_imports_activity_types_from_new_sdk():
    """
    PASS CRITERIA: Activity and ActivityTypes are imported from microsoft_agents.

    Verifies:
    1. Imports from microsoft_agents.activity
    2. Activity and ActivityTypes are available
    """
    source = get_base_chat_bot_source()

    assert "from microsoft_agents.activity import Activity, ActivityTypes" in source, "Activity imports not found"


def test_no_channels_constant_import():
    """
    PASS CRITERIA: BaseChatBot does not import Channels constant.

    Verifies:
    1. No "from botframework.connector import Channels"
    2. Uses string literals for channel IDs instead
    """
    source = get_base_chat_bot_source()

    assert "from botframework.connector import Channels" not in source, "Found Channels import"
    assert "import Channels" not in source, "Found Channels import"


def test_uses_msteams_string_literal():
    """
    PASS CRITERIA: Uses "msteams" string literal instead of Channels.ms_teams.

    Verifies:
    1. String literal "msteams" is used for Teams channel detection
    2. No Channels.ms_teams references
    """
    source = get_base_chat_bot_source()

    assert (
        'channel_id == "msteams"' in source or "channel_id == 'msteams'" in source
    ), "String literal 'msteams' not found for Teams channel detection"
    assert "Channels.ms_teams" not in source, "Found Channels.ms_teams constant usage"


def test_uses_slack_string_literal():
    """
    PASS CRITERIA: Uses "slack" string literal instead of Channels.slack.

    Verifies:
    1. String literal "slack" is used for Slack channel detection
    2. No Channels.slack references
    """
    source = get_base_chat_bot_source()

    assert (
        'channel_id == "slack"' in source or "channel_id == 'slack'" in source
    ), "String literal 'slack' not found for Slack channel detection"
    assert "Channels.slack" not in source, "Found Channels.slack constant usage"


def test_all_channel_checks_use_string_literals():
    """
    PASS CRITERIA: All channel ID checks use string literals.

    Verifies:
    1. No Channels constant is used anywhere
    2. All channel_id comparisons use string literals
    """
    source = get_base_chat_bot_source()

    # Count channel_id comparisons
    channel_checks = source.count("channel_id ==")

    # Verify no Channels. usage exists
    assert "Channels." not in source, "Found Channels constant usage in source"

    # Verify we have the expected channel checks (at least 3: Teams conversation update, Slack message, Teams message)
    assert channel_checks >= 3, f"Expected at least 3 channel_id checks, found {channel_checks}"
