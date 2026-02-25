from unittest.mock import MagicMock

import pytest
from aihub_lib.testing.auth_utils.role_mocks import mock_role_entity_methods  # noqa: F401
from aihub_lib.testing.auth_utils.tenant_mocks import mock_tenant_entity_autouse  # noqa: F401
from aihub_lib.testing.auth_utils.user_mocks import mock_user_entity_autouse  # noqa: F401
from aiohttp import ClientResponse


@pytest.fixture(autouse=True)
def mock_msal_auth(monkeypatch):
    """Mock MSAL authentication to prevent actual HTTP calls to Azure AD."""

    # Mock the MsalAuth.get_access_token method to return a fake token
    async def mock_get_access_token(self, *args, **kwargs):
        return "mock_token_12345"

    monkeypatch.setattr(
        "microsoft_agents.authentication.msal.msal_auth.MsalAuth.get_access_token", mock_get_access_token
    )

    yield


@pytest.fixture(scope="function")
def captured_responses():
    """List to capture bot framework responses for test assertions."""
    responses = []
    return responses


@pytest.fixture(autouse=True)
def mock_aiohttp_requests(monkeypatch, captured_responses):
    """Mock aiohttp requests to prevent DNS resolution failures and capture responses."""

    # Create a mock response that looks like a successful bot framework response
    mock_response = MagicMock(spec=ClientResponse)
    mock_response.status = 200
    mock_response.ok = True
    mock_response.headers = {}

    async def mock_json():
        return {"id": "test_response_id"}

    async def mock_text():
        return '{"id": "test_response_id"}'

    async def mock_read():
        return b'{"id": "test_response_id"}'

    mock_response.json = mock_json
    mock_response.text = mock_text
    mock_response.read = mock_read

    # Create a context manager that returns the mock response and captures requests
    class MockAsyncContextManager:
        def __init__(self, url, **kwargs):
            self.url = url
            self.kwargs = kwargs

        async def __aenter__(self):
            # Capture the request for test assertions (skip typing indicators)
            if "json" in self.kwargs:
                payload = self.kwargs["json"]
                # Only capture message activities, not typing indicators
                if payload.get("type") == "message":
                    # Extract path from URL
                    from collections import namedtuple
                    from urllib.parse import urlparse

                    parsed = urlparse(str(self.url))
                    path = parsed.path

                    # Ensure path has leading slash
                    if path and not path.startswith("/"):
                        path = "/" + path

                    # Store the response info
                    MockedResponse = namedtuple("MockedResponse", ["path", "payload"])
                    response_info = MockedResponse(path=path, payload=payload)
                    captured_responses.append(response_info)

            return mock_response

        async def __aexit__(self, *args):
            pass

    # Mock aiohttp ClientSession.post to return a context manager
    def mock_post(self, url, *args, **kwargs):
        return MockAsyncContextManager(url, **kwargs)

    def mock_get(self, url, *args, **kwargs):
        return MockAsyncContextManager(url, **kwargs)

    def mock_put(self, url, *args, **kwargs):
        return MockAsyncContextManager(url, **kwargs)

    monkeypatch.setattr("aiohttp.ClientSession.post", mock_post)
    monkeypatch.setattr("aiohttp.ClientSession.get", mock_get)
    monkeypatch.setattr("aiohttp.ClientSession.put", mock_put)

    yield
