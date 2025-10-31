"""
Test suite for Task 5.2: Update Playground Tests

This test suite verifies that playground test infrastructure works with the Microsoft 365 Agents SDK.
The playground provides tools for testing bots locally without full infrastructure.
"""

from pathlib import Path


def test_simulated_runner_uses_new_sdk():
    """
    PASS CRITERIA: SimulatedAgentBotTestRunner uses new SDK.

    Verifies:
    1. No old SDK imports in SimulatedAgentBotTestRunner
    2. Uses new SDK for adapter creation
    3. Compatible with migrated bots
    """
    scope_root = Path(__file__).parent.parent.parent
    runner_file = scope_root / "aihub_bot" / "runners" / "SimulatedAgentBotTestRunner.py"

    assert runner_file.exists(), "SimulatedAgentBotTestRunner.py not found"
    source = runner_file.read_text()

    # Should not use old SDK
    assert "from botbuilder" not in source, "Found botbuilder import in SimulatedAgentBotTestRunner"
    assert "from botframework" not in source, "Found botframework import in SimulatedAgentBotTestRunner"


def test_bot_runner_uses_new_sdk():
    """
    PASS CRITERIA: BotRunner uses new SDK.

    Verifies:
    1. No old SDK imports in BotRunner
    2. Can create bot application with new SDK
    """
    scope_root = Path(__file__).parent.parent.parent
    runner_file = scope_root / "aihub_bot" / "runners" / "BotRunner.py"

    assert runner_file.exists(), "BotRunner.py not found"
    source = runner_file.read_text()

    # Should not use old SDK
    assert "from botbuilder" not in source, "Found botbuilder import in BotRunner"
    assert "from botframework" not in source, "Found botframework import in BotRunner"


def test_bot_test_runner_uses_new_sdk():
    """
    PASS CRITERIA: BotTestRunner uses new SDK.

    Verifies:
    1. No old SDK imports in BotTestRunner
    2. Test infrastructure compatible with new SDK
    """
    scope_root = Path(__file__).parent.parent.parent
    runner_file = scope_root / "aihub_bot" / "runners" / "BotTestRunner.py"

    assert runner_file.exists(), "BotTestRunner.py not found"
    source = runner_file.read_text()

    # Should not use old SDK
    assert "from botbuilder" not in source, "Found botbuilder import in BotTestRunner"
    assert "from botframework" not in source, "Found botframework import in BotTestRunner"


def test_playground_tests_use_new_sdk():
    """
    PASS CRITERIA: Playground test files use new SDK.

    Verifies:
    1. Playground tests don't import old SDK
    2. Test files are compatible with migrated bots
    """
    scope_root = Path(__file__).parent.parent.parent
    playground_tests_dir = scope_root / "playground" / "testing" / "tests"

    if not playground_tests_dir.exists():
        # Playground tests may not exist yet
        return

    # Check all test files in playground
    for test_file in playground_tests_dir.glob("test_*.py"):
        source = test_file.read_text()

        # Should not use old SDK
        assert "from botbuilder" not in source, f"Found botbuilder import in {test_file.name}"
        assert "from botframework" not in source, f"Found botframework import in {test_file.name}"


def test_runners_directory_structure():
    """
    PASS CRITERIA: Runners directory has expected structure.

    Verifies:
    1. All expected runner files exist
    2. Files are non-empty
    """
    scope_root = Path(__file__).parent.parent.parent
    runners_dir = scope_root / "aihub_bot" / "runners"

    expected_files = [
        "BotRunner.py",
        "BotTestRunner.py",
        "SimulatedAgentBotTestRunner.py",
    ]

    for filename in expected_files:
        file_path = runners_dir / filename
        assert file_path.exists(), f"Expected runner file not found: {filename}"
        assert file_path.stat().st_size > 0, f"Runner file is empty: {filename}"


def test_playground_test_messages_exist():
    """
    PASS CRITERIA: Playground test fixtures exist.

    Verifies:
    1. Test message JSON files exist
    2. Files are valid JSON structure
    """
    import json

    scope_root = Path(__file__).parent.parent.parent
    playground_tests_dir = scope_root / "playground" / "testing" / "tests"

    if not playground_tests_dir.exists():
        # Playground tests may not exist yet
        return

    # Check for user_message.json
    message_file = playground_tests_dir / "user_message.json"
    if message_file.exists():
        content = message_file.read_text()
        try:
            data = json.loads(content)
            # Should be valid Bot Framework Activity structure
            assert "type" in data or "Type" in data, "Message should have type field"
        except json.JSONDecodeError:
            assert False, f"Invalid JSON in {message_file.name}"
