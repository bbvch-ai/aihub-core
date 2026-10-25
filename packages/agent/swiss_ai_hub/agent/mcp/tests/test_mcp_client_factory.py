import socket
from unittest.mock import patch

import pytest
from fastmcp.client.auth import BearerAuth
from fastmcp.client.transports import SSETransport, StreamableHttpTransport
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


def _transport_auth(client_cls) -> object:
    return client_cls.call_args.args[0].auth


@pytest.fixture
def public_dns(monkeypatch: pytest.MonkeyPatch) -> dict[str, list[str]]:
    """What each host name resolves to; every name the tests use resolves to a public address unless set here."""
    answers: dict[str, list[str]] = {}

    def getaddrinfo(host: str, port: int, **_: object) -> list[tuple]:
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, port)) for ip in answers.get(host, ["93.184.216.34"])]

    monkeypatch.setattr("swiss_ai_hub.core.network.public_host_guard.socket.getaddrinfo", getaddrinfo)
    monkeypatch.setenv("MCP_ALLOWED_PRIVATE_HOSTS", "")
    return answers


@pytest.fixture
def client_cls():
    with patch("swiss_ai_hub.agent.mcp.mcp_client_factory.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        yield mock_client_cls


@pytest.mark.usefixtures("public_dns")
class TestCreate:
    """End-to-end behavior of the public create() context manager."""

    @pytest.mark.asyncio
    async def test_none_mode_passes_no_auth_to_client(self, client_cls):
        config = McpClientConfig(name="srv", url="https://mcp.example.com/mcp", auth_mode="none")

        async with McpClientFactory.create(config) as client:
            assert client is client_cls.return_value

        assert _transport_auth(client_cls) is None

    @pytest.mark.asyncio
    async def test_api_key_path_passes_bearer_to_client(self, client_cls):
        config = McpClientConfig(name="srv", url="https://mcp.example.com/mcp", auth_mode="api_key", api_key="key")

        async with McpClientFactory.create(config):
            pass

        auth = _transport_auth(client_cls)
        assert isinstance(auth, BearerAuth)
        assert auth.token.get_secret_value() == "key"

    @pytest.mark.asyncio
    async def test_user_token_path_passes_resolved_token_to_client(self, client_cls):
        config = McpClientConfig(name="srv", url="https://mcp.example.com/mcp", auth_mode="user_token")

        async with McpClientFactory.create(config, user_token="tok-from-caller"):
            pass

        auth = _transport_auth(client_cls)
        assert isinstance(auth, BearerAuth)
        assert auth.token.get_secret_value() == "tok-from-caller"

    @pytest.mark.asyncio
    async def test_headers_reach_the_transport(self, client_cls):
        config = McpClientConfig(
            name="srv", url="https://mcp.example.com/mcp", auth_mode="none", headers={"X-Tenant": "acme"}
        )

        async with McpClientFactory.create(config):
            pass

        assert client_cls.call_args.args[0].headers == {"X-Tenant": "acme"}

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("url", "transport_type"),
        [("https://mcp.example.com/mcp", StreamableHttpTransport), ("https://mcp.example.com/sse", SSETransport)],
    )
    async def test_the_transport_follows_the_url(self, client_cls, url: str, transport_type: type):
        async with McpClientFactory.create(McpClientConfig(name="srv", url=url, auth_mode="none")):
            pass

        assert type(client_cls.call_args.args[0]) is transport_type


@pytest.mark.usefixtures("public_dns")
class TestOnlyPublicHosts:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "url",
        [
            "http://dagster-webserver:3000/graphql",
            "http://localhost:8000/mcp",
            "http://10.0.0.5/mcp",
            "http://169.254.169.254/latest/meta-data",
            "server.py",
        ],
    )
    async def test_an_internal_url_is_refused_before_connecting(self, client_cls, url: str):
        config = McpClientConfig(name="srv", url=url, auth_mode="none")

        with pytest.raises(ValueError, match="MCP_ALLOWED_PRIVATE_HOSTS"):
            async with McpClientFactory.create(config):
                pass

        client_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_a_public_name_resolving_inside_is_refused(self, client_cls, public_dns: dict[str, list[str]]):
        public_dns["mcp.attacker.example"] = ["172.20.0.4"]
        config = McpClientConfig(name="srv", url="https://mcp.attacker.example/mcp", auth_mode="none")

        with pytest.raises(ValueError, match="172.20.0.4"):
            async with McpClientFactory.create(config):
                pass

    @pytest.mark.asyncio
    async def test_a_host_the_deployment_allows_is_connected_to(self, client_cls, monkeypatch: pytest.MonkeyPatch):
        """The platform's own API serves MCP at /mcp; an operator allows it by its service name."""
        monkeypatch.setenv("MCP_ALLOWED_PRIVATE_HOSTS", "api")
        config = McpClientConfig(name="aihub", url="http://api:8000/mcp", auth_mode="user_token")

        async with McpClientFactory.create(config, user_token="tok"):
            pass

        client_cls.assert_called_once()


class TestHttpClient:
    def test_redirects_are_not_followed(self):
        client = McpClientFactory._http_client_without_redirects(headers={"X": "1"})

        assert client.follow_redirects is False
        assert client.headers["X"] == "1"
        assert client.timeout.read == 300.0
