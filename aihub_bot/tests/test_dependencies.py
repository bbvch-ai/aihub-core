"""
Test suite for Task 1.1: Update Project Dependencies

This test ensures that the migration from Bot Framework SDK to Microsoft 365 Agents SDK
has been completed successfully by verifying package imports.
"""

import pytest


def test_package_imports():
    """
    PASS CRITERIA: All new SDK packages can be imported without errors.

    This test verifies that:
    1. microsoft_agents.hosting.core is importable
    2. microsoft_agents.hosting.aiohttp is importable
    3. microsoft_agents.activity is importable
    4. No botbuilder packages are present
    """
    # Should succeed - new SDK imports
    from microsoft_agents.activity import Activity, ActivityTypes
    from microsoft_agents.hosting.aiohttp import CloudAdapter
    from microsoft_agents.hosting.core import ActivityHandler, TurnContext

    # Verify objects are importable
    assert ActivityHandler is not None
    assert TurnContext is not None
    assert CloudAdapter is not None
    assert Activity is not None
    assert ActivityTypes is not None

    # Should fail - verify old packages are removed
    with pytest.raises(ImportError):
        from botbuilder.core import ActivityHandler  # noqa: F401


def test_poetry_lock_updated():
    """
    PASS CRITERIA: poetry.lock file contains new packages and excludes old ones.

    Verifies that:
    1. poetry.lock exists and is valid
    2. Contains microsoft-agents-* packages
    3. Does not contain botbuilder-* packages
    """
    import tomllib
    from pathlib import Path

    # Read poetry.lock
    lock_path = Path(__file__).parent.parent / "poetry.lock"
    assert lock_path.exists(), "poetry.lock file not found"

    with open(lock_path, "rb") as f:
        lock_data = tomllib.load(f)
    package_names = [pkg["name"] for pkg in lock_data["package"]]

    # Verify new packages are present
    assert "microsoft-agents-hosting-core" in package_names, "microsoft-agents-hosting-core not in lock file"
    assert "microsoft-agents-hosting-aiohttp" in package_names, "microsoft-agents-hosting-aiohttp not in lock file"
    assert "microsoft-agents-activity" in package_names, "microsoft-agents-activity not in lock file"
    assert (
        "microsoft-agents-authentication-msal" in package_names
    ), "microsoft-agents-authentication-msal not in lock file"

    # Verify old packages are removed
    assert "botbuilder-integration-aiohttp" not in package_names, "botbuilder-integration-aiohttp still in lock file"
    assert "botbuilder-core" not in package_names, "botbuilder-core still in lock file"
    assert "botbuilder-schema" not in package_names, "botbuilder-schema still in lock file"


def test_new_sdk_version_compatibility():
    """
    PASS CRITERIA: New SDK packages are compatible with Python 3.13.

    Verifies that:
    1. Packages can be imported in Python 3.13 environment
    2. Basic functionality works
    """
    from microsoft_agents.activity import Activity, ActivityTypes

    # Create a basic activity
    activity = Activity(type=ActivityTypes.message, text="Test message")

    assert activity.type == ActivityTypes.message
    assert activity.text == "Test message"
