"""
Test suite for Task 4.1: Migrate All Controllers

This test verifies that all controller files have been migrated to use the Microsoft 365 Agents SDK
by inspecting the source code for correct imports.
"""

from pathlib import Path


def get_controller_files_source() -> dict[str, str]:
    """Helper to read all controller source files."""
    # Go up from tests/routes to aihub_bot scope root
    scope_root = Path(__file__).parent.parent.parent
    agent_controller = scope_root / "aihub_bot" / "routes" / "agent" / "AgentChatController.py"
    openai_controller = scope_root / "aihub_bot" / "routes" / "openai" / "OpenaiChatController.py"
    bitl_controller = scope_root / "aihub_bot" / "routes" / "bot_in_the_loop" / "BotInTheLoopController.py"

    return {
        "AgentChatController": agent_controller.read_text(),
        "OpenaiChatController": openai_controller.read_text(),
        "BotInTheLoopController": bitl_controller.read_text(),
    }


def test_all_controllers_import_new_sdk():
    """
    PASS CRITERIA: All controllers use new SDK.

    Verifies:
    1. No botbuilder imports in any controller
    2. No botframework imports in any controller
    """
    sources = get_controller_files_source()

    for filename, source in sources.items():
        assert "from botbuilder" not in source, f"Found botbuilder import in {filename}"
        assert "from botframework" not in source, f"Found botframework import in {filename}"


def test_agent_controller_imports():
    """
    PASS CRITERIA: AgentChatController uses new SDK imports.

    Verifies:
    1. Imports CloudAdapter from microsoft_agents
    2. No botbuilder.integration.aiohttp import
    """
    sources = get_controller_files_source()
    source = sources["AgentChatController"]

    assert "from microsoft_agents.hosting.aiohttp import CloudAdapter" in source, "Missing new SDK CloudAdapter import"
    assert "from botbuilder.integration.aiohttp" not in source, "Found old botbuilder.integration.aiohttp import"


def test_openai_controller_imports():
    """
    PASS CRITERIA: OpenaiChatController uses new SDK imports.

    Verifies:
    1. Imports CloudAdapter from microsoft_agents
    2. No botbuilder.integration.aiohttp import
    """
    sources = get_controller_files_source()
    source = sources["OpenaiChatController"]

    assert "from microsoft_agents.hosting.aiohttp import CloudAdapter" in source, "Missing new SDK CloudAdapter import"
    assert "from botbuilder.integration.aiohttp" not in source, "Found old botbuilder.integration.aiohttp import"


def test_bot_in_the_loop_controller_imports():
    """
    PASS CRITERIA: BotInTheLoopController uses new SDK imports.

    Verifies:
    1. Imports CloudAdapter from microsoft_agents
    2. No botbuilder.integration.aiohttp import
    """
    sources = get_controller_files_source()
    source = sources["BotInTheLoopController"]

    assert "from microsoft_agents.hosting.aiohttp import CloudAdapter" in source, "Missing new SDK CloudAdapter import"
    assert "from botbuilder.integration.aiohttp" not in source, "Found old botbuilder.integration.aiohttp import"


def test_controller_type_annotations():
    """
    PASS CRITERIA: Controllers use CloudAdapter type correctly.

    Verifies:
    1. CloudAdapter type is used in type annotations
    2. adapter.process() method is called correctly
    """
    sources = get_controller_files_source()

    # All controllers should use CloudAdapter type annotation
    for filename, source in sources.items():
        assert "CloudAdapter" in source, f"CloudAdapter not found in {filename}"
        assert "adapter.process(" in source, f"adapter.process() not found in {filename}"
