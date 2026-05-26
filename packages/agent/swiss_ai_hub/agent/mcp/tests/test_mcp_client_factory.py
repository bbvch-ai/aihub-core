from unittest.mock import patch

import pytest
from fastmcp.client.auth import BearerAuth
from swiss_ai_hub.core.mcp.mcp_client_config import McpClientConfig

from swiss_ai_hub.agent.mcp.mcp_client_factory import McpClientFactory


class TestResolveAuth:
    """Pure-function tests of the auth resolution rules — no FastMCP client construction."""

    def test_none_mode_returns_no_auth(self):
        config = McpClientConfig(name="srv", url="https://mcp.example.com/mcp", auth_mode="none")
        assert McpClientFactory._resolve_auth(config, user_token=None) is None

    def test_none_mode_ignores_api_key_and_user_token(self):
        """'none' means no credentials — neither a configured key nor a forwarded token leaks in."""
        config = McpClientConfig(
            name="srv",
            url="https://mcp.example.com/mcp",
            auth_mode="none",
            api_key="should-be-ignored",
        )
        assert McpClientFactory._resolve_auth(config, user_token="user-token-abc") is None

    def test_api_key_mode_uses_config_api_key(self):
        config = McpClientConfig(
            name="srv",
            url="https://mcp.example.com/mcp",
            auth_mode="api_key",
            api_key="static-key-123",
        )
        auth = McpClientFactory._resolve_auth(config, user_token=None)
        assert isinstance(auth, BearerAuth)
        assert auth.token.get_secret_value() == "static-key-123"

    def test_api_key_mode_ignores_user_token(self):
        """api_key mode must not silently pick up a user token — that would be a confusing surprise."""
        config = McpClientConfig(
            name="srv",
            url="https://mcp.example.com/mcp",
            auth_mode="api_key",
            api_key="static-key-123",
        )
        auth = McpClientFactory._resolve_auth(config, user_token="user-token-abc")
        assert isinstance(auth, BearerAuth)
        assert auth.token.get_secret_value() == "static-key-123"

    def test_api_key_mode_without_key_raises(self):
        """Misconfiguration — api_key mode with no key should fail loudly, not silently send no auth."""
        config = McpClientConfig(name="jira", url="https://mcp.example.com/mcp", auth_mode="api_key")
        with pytest.raises(ValueError, match="'jira'.*api_key"):
            McpClientFactory._resolve_auth(config, user_token=None)

    def test_default_auth_mode_uses_api_key(self):
        """A config that omits auth_mode keeps using its api_key — existing connections stay working."""
        config = McpClientConfig(name="srv", url="https://mcp.example.com/mcp", api_key="legacy-key")
        auth = McpClientFactory._resolve_auth(config, user_token=None)
        assert isinstance(auth, BearerAuth)
        assert auth.token.get_secret_value() == "legacy-key"

    def test_user_token_mode_uses_user_token(self):
        config = McpClientConfig(
            name="srv",
            url="https://mcp.example.com/mcp",
            auth_mode="user_token",
            api_key="should-be-ignored",
        )
        auth = McpClientFactory._resolve_auth(config, user_token="user-token-abc")
        assert isinstance(auth, BearerAuth)
        assert auth.token.get_secret_value() == "user-token-abc"

    def test_user_token_mode_without_token_raises(self):
        """Misconfiguration — refuse to fall back to the static key, which would mask the actor."""
        config = McpClientConfig(
            name="jira",
            url="https://mcp.example.com/mcp",
            auth_mode="user_token",
            api_key="static-fallback",
        )
        with pytest.raises(ValueError, match="'jira'.*user_token"):
            McpClientFactory._resolve_auth(config, user_token=None)

    def test_user_token_mode_empty_string_raises(self):
        """An empty token is just as broken as a missing token — don't ship an Authorization: Bearer line."""
        config = McpClientConfig(name="srv", url="https://mcp.example.com/mcp", auth_mode="user_token")
        with pytest.raises(ValueError, match="user_token"):
            McpClientFactory._resolve_auth(config, user_token="")


class TestCreate:
    """End-to-end behavior of the public create() context manager."""

    @pytest.mark.asyncio
    async def test_none_mode_passes_no_auth_to_client(self):
        config = McpClientConfig(name="srv", url="https://mcp.example.com/mcp", auth_mode="none")

        with patch("swiss_ai_hub.agent.mcp.mcp_client_factory.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            async with McpClientFactory.create(config) as client:
                assert client is mock_client

            assert mock_client_cls.call_args.kwargs["auth"] is None

    @pytest.mark.asyncio
    async def test_api_key_path_passes_bearer_to_client(self):
        config = McpClientConfig(name="srv", url="https://mcp.example.com/mcp", auth_mode="api_key", api_key="key")

        with patch("swiss_ai_hub.agent.mcp.mcp_client_factory.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            async with McpClientFactory.create(config) as client:
                assert client is mock_client

            kwargs = mock_client_cls.call_args.kwargs
            assert isinstance(kwargs["auth"], BearerAuth)
            assert kwargs["auth"].token.get_secret_value() == "key"

    @pytest.mark.asyncio
    async def test_user_token_path_passes_resolved_token_to_client(self):
        config = McpClientConfig(
            name="srv",
            url="https://mcp.example.com/mcp",
            auth_mode="user_token",
        )

        with patch("swiss_ai_hub.agent.mcp.mcp_client_factory.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None

            async with McpClientFactory.create(config, user_token="tok-from-caller"):
                pass

            kwargs = mock_client_cls.call_args.kwargs
            assert isinstance(kwargs["auth"], BearerAuth)
            assert kwargs["auth"].token.get_secret_value() == "tok-from-caller"
