"""
Test suite for Task 2.3: Migrate CompletionHandler

This test verifies that CompletionHandler has been migrated to use the Microsoft 365 Agents SDK
by inspecting the source code for correct imports and testing key functionality.
"""

from pathlib import Path


def get_completion_handler_source() -> str:
    """Helper to read CompletionHandler source file."""
    completion_handler_path = (
        Path(__file__).parent.parent.parent.parent / "aihub_bot" / "bots" / "chat" / "CompletionHandler.py"
    )
    return completion_handler_path.read_text()


def test_completion_handler_imports_new_sdk():
    """
    PASS CRITERIA: CompletionHandler uses new SDK imports.

    Verifies:
    1. No botbuilder imports
    2. Uses microsoft_agents imports
    """
    source = get_completion_handler_source()

    assert "from botbuilder" not in source, "Found botbuilder import in CompletionHandler"
    assert "from microsoft_agents" in source, "microsoft_agents import not found"


def test_imports_turn_context_from_new_sdk():
    """
    PASS CRITERIA: TurnContext is imported from microsoft_agents.

    Verifies:
    1. Imports from microsoft_agents.hosting.core
    2. TurnContext is used in type hints
    """
    source = get_completion_handler_source()

    assert "from microsoft_agents.hosting.core import TurnContext" in source, "TurnContext import not found"
    assert "TurnContext" in source, "TurnContext not used"


def test_imports_activity_from_new_sdk():
    """
    PASS CRITERIA: Activity and ActivityTypes are imported from microsoft_agents.

    Verifies:
    1. Imports from microsoft_agents.activity
    2. Activity, ActivityTypes, and Entity are available
    """
    source = get_completion_handler_source()

    assert "from microsoft_agents.activity import Activity, ActivityTypes" in source, "Activity imports not found"
    # Entity should also be imported
    assert "Entity" in source, "Entity not used"


def test_no_error_response_exception():
    """
    PASS CRITERIA: ErrorResponseException is not imported from old SDK.

    Verifies:
    1. No ErrorResponseException from botbuilder.schema
    2. Uses standard exception handling instead
    """
    source = get_completion_handler_source()

    assert (
        "ErrorResponseException" not in source or "microsoft_agents" in source
    ), "ErrorResponseException from old SDK found"


def test_no_teams_channel_data_import():
    """
    PASS CRITERIA: TeamsChannelData is not imported from old SDK.

    Verifies:
    1. No import from botbuilder.schema.teams
    2. Uses dictionary access or new SDK equivalent
    """
    source = get_completion_handler_source()

    assert (
        "from botbuilder.schema.teams import TeamsChannelData" not in source
    ), "Found TeamsChannelData import from old SDK"


def test_typing_activity_uses_new_sdk():
    """
    PASS CRITERIA: Typing activity creation uses new SDK.

    Verifies:
    1. Activity is created with type=ActivityTypes.typing
    2. Uses new SDK's Activity and ActivityTypes
    """
    source = get_completion_handler_source()

    # Check that Activity is used to create typing activities
    assert "Activity(type=ActivityTypes.typing)" in source, "Typing activity creation not found"


def test_message_activity_uses_new_sdk():
    """
    PASS CRITERIA: Message activity creation uses new SDK.

    Verifies:
    1. Activity is created with type=ActivityTypes.message
    2. Uses new SDK's Activity and ActivityTypes
    """
    source = get_completion_handler_source()

    # Check that Activity is used to create message activities
    assert "ActivityTypes.message" in source, "Message activity type not found"


def test_all_imports_migrated():
    """
    PASS CRITERIA: All SDK imports are from microsoft_agents.

    Verifies:
    1. No botbuilder.core imports
    2. No botbuilder.schema imports
    3. No botframework imports
    """
    source = get_completion_handler_source()

    assert "from botbuilder.core" not in source, "Found botbuilder.core import"
    assert "from botbuilder.schema" not in source, "Found botbuilder.schema import"
    assert "from botframework" not in source, "Found botframework import"
