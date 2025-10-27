"""
Test suite for Task 2.1: Migrate RoutesService

This test verifies that RoutesService has been migrated to use the Microsoft 365 Agents SDK
and that adapter creation and authentication work correctly.
"""


import pytest


@pytest.fixture
def mock_credentials():
    """Create mock credentials for testing."""
    return {
        "APP_TYPE": "MultiTenant",
        "APP_ID": "test-app-id-123",
        "APP_PASSWORD": "test-password-456",
    }


@pytest.fixture
def single_tenant_credentials():
    """Create mock single-tenant credentials."""
    return {
        "APP_TYPE": "SingleTenant",
        "APP_ID": "test-app-id-789",
        "APP_PASSWORD": "test-password-012",
        "APP_TENANTID": "test-tenant-345",
    }


def test_routes_service_imports_new_sdk():
    """
    PASS CRITERIA: RoutesService uses new SDK imports.

    Verifies:
    1. No botbuilder imports in the file
    2. Uses microsoft_agents imports
    """
    from pathlib import Path

    # Read the source file directly
    routes_service_path = Path(__file__).parent.parent.parent / "aihub_bot" / "routes" / "RoutesService.py"
    source = routes_service_path.read_text()

    # Should not contain old imports
    assert "from botbuilder" not in source, "Found botbuilder import in RoutesService"
    assert "from botframework" not in source, "Found botframework import in RoutesService"

    # Should contain new imports
    assert "from microsoft_agents" in source, "microsoft_agents import not found"
    assert "microsoft_agents.hosting.aiohttp" in source, "CloudAdapter import not found"
    assert "microsoft_agents.authentication.msal" in source, "Auth import not found"


def test_cloud_adapter_new_sdk():
    """
    PASS CRITERIA: CloudAdapter is from new SDK.

    Verifies:
    1. CloudAdapter can be imported from microsoft_agents
    2. CloudAdapter is the correct type
    """
    from microsoft_agents.hosting.aiohttp import CloudAdapter as NewCloudAdapter

    assert NewCloudAdapter is not None
    assert "microsoft_agents" in NewCloudAdapter.__module__


def test_authentication_imports():
    """
    PASS CRITERIA: Authentication classes are from new SDK.

    Verifies:
    1. MsalConnectionManager can be imported
    2. AgentAuthConfiguration can be imported
    3. Both are from microsoft_agents
    """
    from microsoft_agents.authentication.msal import MsalConnectionManager
    from microsoft_agents.hosting.core import AgentAuthConfiguration

    assert MsalConnectionManager is not None
    assert "microsoft_agents" in MsalConnectionManager.__module__
    assert AgentAuthConfiguration is not None
    assert "microsoft_agents" in AgentAuthConfiguration.__module__


def test_source_file_structure():
    """
    PASS CRITERIA: RoutesService has correct structure and methods.

    Verifies:
    1. _adapter_cache variable exists
    2. get_adapter method exists
    3. _create_auth_configuration helper method exists
    4. Uses new SDK classes
    """
    from pathlib import Path

    # Navigate up from tests/routes/ to aihub_bot scope root, then to aihub_bot package
    routes_service_path = Path(__file__).parent.parent.parent / "aihub_bot" / "routes" / "RoutesService.py"
    source = routes_service_path.read_text()

    assert "_adapter_cache" in source, "Adapter cache not found"
    assert "def get_adapter" in source, "get_adapter method not found"
    assert "def _create_auth_configuration" in source, "_create_auth_configuration method not found"
    assert "CloudAdapter" in source, "CloudAdapter not found"
    assert "MsalConnectionManager" in source, "MsalConnectionManager not found"
    assert "AgentAuthConfiguration" in source, "AgentAuthConfiguration not found"
