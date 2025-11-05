"""
Shared pytest configuration and fixtures for bot tests.

This module provides common test fixtures that prevent external service dependencies,
particularly Microsoft authentication services and HTTP calls.
"""

import pytest


@pytest.fixture
def mock_aiohttp_requests(monkeypatch):
    """
    Mock aiohttp HTTP requests to prevent real network calls.

    ### What
    - Patches aiohttp ClientSession methods to return mock responses
    - Prevents the bot from making real HTTP calls when sending activities

    ### Why
    - The microsoft-agents SDK uses aiohttp to send bot responses
    - Tests use fake serviceUrl endpoints that don't exist
    - We want to test bot logic without network dependencies

    ### How
    - Mocks ClientSession._request to return a successful mock response
    - NOT applied automatically (autouse=False) - use explicit fixture for routing tests

    ### Note
    - For tests that need to capture bot responses, use patch_aiohttp_routing instead
    - This fixture is for simple tests that just need to prevent network calls
    """
    try:
        import aiohttp
        from unittest.mock import AsyncMock

        async def fake_request(self, method, url, **kwargs):
            """Mock aiohttp request that returns a successful response."""
            # Create a mock response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.reason = "OK"
            mock_response.headers = {}
            mock_response.text = AsyncMock(return_value="{}")
            mock_response.json = AsyncMock(return_value={})
            mock_response.read = AsyncMock(return_value=b"{}")

            # Mock the context manager behavior
            mock_response.__aenter__ = AsyncMock(return_value=mock_response)
            mock_response.__aexit__ = AsyncMock(return_value=None)

            return mock_response

        # Patch the _request method which all HTTP methods use internally
        monkeypatch.setattr(aiohttp.ClientSession, "_request", fake_request)
    except ImportError:
        # If aiohttp isn't installed, skip this fixture
        pass


@pytest.fixture(autouse=True)
def mock_msal_auth(monkeypatch):
    """
    Mock MSAL authentication to prevent real HTTP calls to Microsoft authentication servers.

    ### What
    - Automatically patches the MsalAuth.get_access_token method for all tests
    - Returns a fake access token without making external HTTP requests

    ### Why
    - The microsoft-agents SDK attempts to authenticate with real Microsoft services
    - Tests use fake credentials that would fail authentication
    - We want to test bot logic, not Microsoft's authentication service
    - Prevents test failures due to network issues or invalid test credentials

    ### How
    - Uses pytest's monkeypatch to replace the get_access_token method
    - Returns a static fake token that's sufficient for testing
    - Applied automatically to all tests via autouse=True
    """

    async def fake_get_access_token(self, resource_url: str, scopes: list[str], force_refresh: bool = False) -> str:
        """
        Fake token acquisition that returns a test token without external HTTP calls.

        Args:
            resource_url: The resource URL requesting the token (e.g., https://api.botframework.com)
            scopes: List of OAuth scopes being requested
            force_refresh: Whether to force refresh the token

        Returns:
            A fake access token string for testing
        """
        return "fake-test-access-token"

    # Import here to avoid import errors if the package isn't installed
    try:
        from microsoft_agents.authentication.msal import msal_auth

        # Patch the get_access_token method to use our fake implementation
        monkeypatch.setattr(msal_auth.MsalAuth, "get_access_token", fake_get_access_token)
    except ImportError:
        # If microsoft-agents isn't installed, skip this fixture
        # This allows tests to run in environments without the SDK
        pass


@pytest.fixture(autouse=True)
def mock_msal_auth_async(monkeypatch):
    """
    Mock async MSAL authentication to prevent real HTTP calls to Microsoft authentication servers.

    This is the async version of mock_msal_auth for any async authentication flows.
    """

    async def fake_get_access_token_async(
        self, resource_url: str, scopes: list[str], force_refresh: bool = False
    ) -> str:
        """
        Async fake token acquisition that returns a test token without external HTTP calls.

        Args:
            resource_url: The resource URL requesting the token
            scopes: List of OAuth scopes being requested
            force_refresh: Whether to force refresh the token

        Returns:
            A fake access token string for testing
        """
        return "fake-test-access-token"

    # Import here to avoid import errors if the package isn't installed
    try:
        from microsoft_agents.authentication.msal import msal_auth

        # Check if there's an async version and patch it
        if hasattr(msal_auth.MsalAuth, "get_access_token_async"):
            monkeypatch.setattr(msal_auth.MsalAuth, "get_access_token_async", fake_get_access_token_async)
    except ImportError:
        # If microsoft-agents isn't installed, skip this fixture
        pass
