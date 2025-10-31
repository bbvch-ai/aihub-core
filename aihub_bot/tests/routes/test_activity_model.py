"""
Test suite for Task 4.2: Migrate Activity Models

This test verifies that activity_model.py has been migrated to use the Microsoft 365 Agents SDK
by inspecting the source code for correct imports.
"""

from pathlib import Path


def get_activity_model_source() -> str:
    """Helper to read activity_model.py source file."""
    # Go up from tests/routes to aihub_bot scope root
    scope_root = Path(__file__).parent.parent.parent
    activity_model_file = scope_root / "aihub_bot" / "routes" / "activity_model.py"
    return activity_model_file.read_text()


def test_activity_model_imports_new_sdk():
    """
    PASS CRITERIA: activity_model uses new SDK.

    Verifies:
    1. No botbuilder.schema imports
    2. Uses microsoft_agents.activity
    """
    source = get_activity_model_source()

    assert "from botbuilder.schema" not in source, "Found botbuilder.schema import"
    assert "from microsoft_agents.activity" in source, "Missing microsoft_agents.activity import"


def test_no_old_sdk_types():
    """
    PASS CRITERIA: No imports from old SDK.

    Verifies:
    1. No botbuilder imports at all
    """
    source = get_activity_model_source()

    assert "from botbuilder" not in source, "Found botbuilder import"


def test_activity_model_types_compatible():
    """
    PASS CRITERIA: Activity models are compatible with new SDK.

    Verifies:
    1. Can import the ActivityModel
    2. ActivityModel is usable
    """
    from aihub_bot.routes.activity_model import ActivityModel

    # Should be able to import without errors
    assert ActivityModel is not None
    # ActivityModel should be a pydantic model
    assert hasattr(ActivityModel, "__fields__") or hasattr(ActivityModel, "model_fields")
