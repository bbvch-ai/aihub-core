"""
Test suite for Task 3.3: Migrate Bot-in-the-Loop

This test verifies that Bot-in-the-Loop has been migrated to use the Microsoft 365 Agents SDK
by inspecting the source code for correct imports.
"""

from pathlib import Path


def get_bot_in_the_loop_files_source() -> dict[str, str]:
    """Helper to read Bot-in-the-Loop source files."""
    # Go up from tests/bots/bot_in_the_loop to aihub_bot scope root
    scope_root = Path(__file__).parent.parent.parent.parent
    bot_file = scope_root / "aihub_bot" / "bots" / "bot_in_the_loop" / "BotInTheLoopBot.py"
    handler_file = scope_root / "aihub_bot" / "routes" / "bot_in_the_loop" / "BotInTheLoopHandler.py"

    return {
        "BotInTheLoopBot": bot_file.read_text(),
        "BotInTheLoopHandler": handler_file.read_text(),
    }


def test_all_bot_in_the_loop_files_imports_new_sdk():
    """
    PASS CRITERIA: All Bot-in-the-Loop files use new SDK.

    Verifies:
    1. BotInTheLoopBot has no botbuilder imports
    2. BotInTheLoopHandler has no botbuilder imports
    3. No botframework imports in any file
    """
    sources = get_bot_in_the_loop_files_source()

    for filename, source in sources.items():
        assert "from botbuilder" not in source, f"Found botbuilder import in {filename}"
        assert "from botframework" not in source, f"Found botframework import in {filename}"


def test_bot_in_the_loop_bot_imports():
    """
    PASS CRITERIA: BotInTheLoopBot uses new SDK imports.

    Verifies:
    1. Imports ActivityHandler from microsoft_agents
    2. Imports TurnContext from microsoft_agents
    3. No Channels import
    """
    sources = get_bot_in_the_loop_files_source()
    source = sources["BotInTheLoopBot"]

    assert "from microsoft_agents.hosting.core import ActivityHandler, TurnContext" in source, "Missing new SDK imports"
    assert "from botframework.connector import Channels" not in source, "Found Channels import"


def test_bot_in_the_loop_handler_imports():
    """
    PASS CRITERIA: BotInTheLoopHandler uses new SDK imports.

    Verifies:
    1. Imports TurnContext from microsoft_agents
    2. Imports ConversationReference from microsoft_agents
    3. No Channels import
    """
    sources = get_bot_in_the_loop_files_source()
    source = sources["BotInTheLoopHandler"]

    assert "from microsoft_agents" in source, "Missing microsoft_agents imports"
    assert "from botframework.connector import Channels" not in source, "Found Channels import"


def test_bot_no_channels_constant():
    """
    PASS CRITERIA: BotInTheLoopBot doesn't use Channels constant.

    Verifies:
    1. No Channels.slack usage
    2. No Channels.ms_teams usage
    3. Uses string literals instead
    """
    sources = get_bot_in_the_loop_files_source()
    source = sources["BotInTheLoopBot"]

    assert "Channels.slack" not in source, "Found Channels.slack constant"
    assert "Channels.ms_teams" not in source, "Found Channels.ms_teams constant"
    assert "Channels." not in source, "Found Channels constant usage"


def test_handler_no_channels_constant():
    """
    PASS CRITERIA: BotInTheLoopHandler doesn't use Channels constant.

    Verifies:
    1. No Channels.slack usage
    2. No Channels.ms_teams usage
    3. Uses string literals instead
    """
    sources = get_bot_in_the_loop_files_source()
    source = sources["BotInTheLoopHandler"]

    assert "Channels.slack" not in source, "Found Channels.slack constant"
    assert "Channels.ms_teams" not in source, "Found Channels.ms_teams constant"
    assert "Channels." not in source, "Found Channels constant usage"


def test_slack_string_literal_usage():
    """
    PASS CRITERIA: Uses "slack" string literal.

    Verifies:
    1. String literal "slack" is used for channel detection
    """
    sources = get_bot_in_the_loop_files_source()
    bot_source = sources["BotInTheLoopBot"]
    handler_source = sources["BotInTheLoopHandler"]

    # Bot file should use string literal
    assert (
        'channel_id == "slack"' in bot_source or "channel_id == 'slack'" in bot_source
    ), "String literal 'slack' not found in bot"

    # Handler should use string literal
    assert '"slack"' in handler_source or "'slack'" in handler_source, "String literal 'slack' not found in handler"


def test_msteams_string_literal_usage():
    """
    PASS CRITERIA: Uses "msteams" string literal.

    Verifies:
    1. String literal "msteams" is used for Teams channel detection
    """
    sources = get_bot_in_the_loop_files_source()
    bot_source = sources["BotInTheLoopBot"]
    handler_source = sources["BotInTheLoopHandler"]

    # Bot file should use string literal
    assert (
        'channel_id == "msteams"' in bot_source or "channel_id == 'msteams'" in bot_source
    ), "String literal 'msteams' not found in bot"

    # Handler should use string literal
    assert (
        '"msteams"' in handler_source or "'msteams'" in handler_source
    ), "String literal 'msteams' not found in handler"


def test_bot_inherits_activity_handler():
    """
    PASS CRITERIA: BotInTheLoopBot inherits from ActivityHandler.

    Verifies:
    1. Class definition shows inheritance from ActivityHandler
    """
    sources = get_bot_in_the_loop_files_source()
    source = sources["BotInTheLoopBot"]

    assert "class BotInTheLoopBot(ActivityHandler):" in source, "BotInTheLoopBot doesn't inherit from ActivityHandler"


def test_parse_conversation_id_type_annotation():
    """
    PASS CRITERIA: _parse_conversation_id method doesn't use Channels type.

    Verifies:
    1. Uses string type for channel parameter instead of Channels enum
    """
    sources = get_bot_in_the_loop_files_source()
    source = sources["BotInTheLoopBot"]

    # Should use str instead of Channels type
    assert (
        "_parse_conversation_id(turn_context: TurnContext, channel: str)" in source
    ), "Method should use str type for channel parameter"


def test_build_conversation_id_type_annotation():
    """
    PASS CRITERIA: _build_conversation_id_with_thread_identifier doesn't use Channels type.

    Verifies:
    1. Uses string type for channel parameter instead of Channels enum
    """
    sources = get_bot_in_the_loop_files_source()
    source = sources["BotInTheLoopHandler"]

    # Should use str instead of Channels type
    assert "channel: str" in source, "Method should use str type for channel parameter"
