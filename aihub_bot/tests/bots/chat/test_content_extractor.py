"""
Test suite for Task 2.4: Migrate ContentExtractor

This test verifies that ContentExtractor has been migrated to use the Microsoft 365 Agents SDK
by inspecting the source code for correct imports and channel ID usage.
"""

from pathlib import Path


def get_content_extractor_source() -> str:
    """Helper to read ContentExtractor source file."""
    content_extractor_path = (
        Path(__file__).parent.parent.parent.parent / "aihub_bot" / "bots" / "chat" / "ContentExtractor.py"
    )
    return content_extractor_path.read_text()


def test_content_extractor_imports_new_sdk():
    """
    PASS CRITERIA: ContentExtractor uses new SDK imports.

    Verifies:
    1. No botbuilder imports
    2. Uses microsoft_agents imports
    3. No botframework imports
    """
    source = get_content_extractor_source()

    assert "from botbuilder" not in source, "Found botbuilder import in ContentExtractor"
    assert "from botframework" not in source, "Found botframework import in ContentExtractor"
    assert "from microsoft_agents" in source, "microsoft_agents import not found"


def test_imports_activity_from_new_sdk():
    """
    PASS CRITERIA: Activity and Attachment are imported from microsoft_agents.

    Verifies:
    1. Imports from microsoft_agents.activity
    2. Activity and Attachment are available
    """
    source = get_content_extractor_source()

    assert (
        "from microsoft_agents.activity import Activity, Attachment" in source
    ), "Activity/Attachment imports not found"


def test_no_channels_import():
    """
    PASS CRITERIA: Channels is not imported from old SDK.

    Verifies:
    1. No import from botframework.connector
    2. No Channels constant usage
    """
    source = get_content_extractor_source()

    assert "from botframework.connector import Channels" not in source, "Found Channels import"
    assert "import Channels" not in source, "Found Channels import"


def test_file_source_enum_uses_string_literals():
    """
    PASS CRITERIA: FileSource enum uses string literals instead of Channels constants.

    Verifies:
    1. FileSource.SLACK uses string literal "slack"
    2. FileSource.TEAMS uses string literal "msteams"
    3. No Channels.slack or Channels.ms_teams
    """
    source = get_content_extractor_source()

    # Check that FileSource enum exists and uses string literals
    assert "class FileSource(Enum):" in source, "FileSource enum not found"
    assert 'SLACK = "slack"' in source, "SLACK enum member doesn't use string literal"
    assert 'TEAMS = "msteams"' in source, "TEAMS enum member doesn't use string literal"

    # Verify no Channels constants used
    assert "Channels.slack" not in source, "Found Channels.slack constant usage"
    assert "Channels.ms_teams" not in source, "Found Channels.ms_teams constant usage"


def test_teams_channel_check_uses_string_literal():
    """
    PASS CRITERIA: Teams channel checks use "msteams" string literal.

    Verifies:
    1. channel_id == "msteams" is used
    2. No Channels.ms_teams references
    """
    source = get_content_extractor_source()

    assert (
        'channel_id == "msteams"' in source or "channel_id == 'msteams'" in source
    ), "String literal 'msteams' not found for Teams channel detection"
    assert "Channels.ms_teams" not in source, "Found Channels.ms_teams constant usage"


def test_all_channel_checks_use_string_literals():
    """
    PASS CRITERIA: All channel ID checks use string literals.

    Verifies:
    1. No Channels constant is used anywhere in comparisons
    2. All channel_id comparisons use string literals
    """
    source = get_content_extractor_source()

    # Verify no Channels. usage exists
    assert "Channels." not in source, "Found Channels constant usage in source"


def test_activity_type_annotations():
    """
    PASS CRITERIA: Activity type annotations are correct.

    Verifies:
    1. Methods accept Activity parameter
    2. Activity is from microsoft_agents
    """
    source = get_content_extractor_source()

    # Check that Activity is used in type annotations
    assert ": Activity" in source or "(activity: Activity)" in source, "Activity type annotation not found"


def test_attachment_type_annotations():
    """
    PASS CRITERIA: Attachment type annotations are correct.

    Verifies:
    1. Methods accept Attachment parameter
    2. Attachment is from microsoft_agents
    """
    source = get_content_extractor_source()

    # Check that Attachment is used in type annotations
    assert ": Attachment" in source or "(attachment: Attachment)" in source, "Attachment type annotation not found"


def test_all_imports_migrated():
    """
    PASS CRITERIA: All SDK imports are from microsoft_agents.

    Verifies:
    1. No botbuilder.schema imports
    2. No botframework imports
    """
    source = get_content_extractor_source()

    assert "from botbuilder.schema" not in source, "Found botbuilder.schema import"
    assert "from botframework" not in source, "Found botframework import"
