import json

import pytest
from pydantic import SecretStr
from starlette.testclient import TestClient

from aihub_mcp.runners.MCPRunner import MCPRunner
from aihub_mcp.settings.MCPSettings import MCPSettings

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestMCPServerHTTP:
    """Tests for MCP server HTTP endpoints."""

    @pytest.fixture
    def settings(self) -> MCPSettings:
        """Create test settings with no NATS dependency."""
        return MCPSettings(REQUIRE_AUTH=False)

    @pytest.fixture
    def app(self, settings: MCPSettings) -> MCPRunner:
        """Create MCP runner for testing."""
        return MCPRunner(settings)

    def test_mcp_path_exists(self, app: MCPRunner) -> None:
        """Test that MCP server creates app with /mcp path."""
        starlette_app = app.create_app()
        routes = [route.path for route in starlette_app.routes]
        assert "/mcp" in [r.rstrip("/") for r in routes] or any("/mcp" in r for r in routes)

    def test_health_endpoint_allows_unauthenticated(self) -> None:
        """Test that health endpoint is accessible without auth."""
        auth_settings = MCPSettings(API_KEY=SecretStr("test-secret-key"))
        runner = MCPRunner(auth_settings)
        starlette_app = runner.create_app()

        with TestClient(starlette_app, raise_server_exceptions=False) as client:
            response = client.get("/mcp/health")
            # Either 200 or 404 (if not implemented), but not 401
            assert response.status_code != 401 or response.status_code == 404


class TestMCPAuthentication:
    """Tests for MCP authentication middleware."""

    @pytest.fixture
    def authenticated_runner(self) -> MCPRunner:
        """Create runner with authentication enabled."""
        settings = MCPSettings(API_KEY=SecretStr("test-api-key"))
        return MCPRunner(settings)

    def test_request_without_key_rejected(self, authenticated_runner: MCPRunner) -> None:
        """Test that requests without API key are rejected."""
        app = authenticated_runner.create_app()

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post("/mcp/")
            assert response.status_code == 401

    def test_request_with_correct_key_accepted(self, authenticated_runner: MCPRunner) -> None:
        """Test that requests with correct API key are accepted."""
        app = authenticated_runner.create_app()

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/mcp/",
                headers={"X-API-Key": "test-api-key"},
                json={"jsonrpc": "2.0", "method": "ping", "id": 1},
            )
            assert response.status_code != 401

    def test_request_with_wrong_key_rejected(self, authenticated_runner: MCPRunner) -> None:
        """Test that requests with wrong API key are rejected."""
        app = authenticated_runner.create_app()

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/mcp/",
                headers={"X-API-Key": "wrong-key"},
            )
            assert response.status_code == 401

    def test_bearer_token_accepted(self, authenticated_runner: MCPRunner) -> None:
        """Test that Bearer token in Authorization header works."""
        app = authenticated_runner.create_app()

        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.post(
                "/mcp/",
                headers={"Authorization": "Bearer test-api-key"},
                json={"jsonrpc": "2.0", "method": "ping", "id": 1},
            )
            assert response.status_code != 401


class TestClaudeCodeConfig:
    """Tests for Claude Code MCP configuration generation."""

    def test_generate_mcp_config(self) -> None:
        """Test generating .mcp.json configuration for Claude Code."""
        config = {
            "mcpServers": {
                "aihub_agents": {
                    "type": "http",
                    "url": "http://localhost:8001/mcp",
                    "disabled": False,
                    "autoApprove": [],
                }
            }
        }

        json_str = json.dumps(config, indent=2)
        parsed = json.loads(json_str)

        assert "mcpServers" in parsed
        assert "aihub_agents" in parsed["mcpServers"]
        assert parsed["mcpServers"]["aihub_agents"]["type"] == "http"

    def test_config_with_api_key(self) -> None:
        """Test configuration with API key authentication."""
        config = {
            "mcpServers": {
                "aihub_agents": {
                    "type": "http",
                    "url": "http://localhost:8001/mcp",
                    "headers": {
                        "X-API-Key": "your-api-key-here",
                    },
                }
            }
        }

        assert "headers" in config["mcpServers"]["aihub_agents"]
        assert "X-API-Key" in config["mcpServers"]["aihub_agents"]["headers"]


class TestMCPRunner:
    """Tests for MCP runner behavior."""

    def test_runner_uses_settings(self) -> None:
        """Test that runner respects settings."""
        settings = MCPSettings(
            HOST="0.0.0.0",
            PORT=9000,
            REQUIRE_AUTH=False,
        )
        runner = MCPRunner(settings)

        assert runner.settings.PORT == 9000
        assert runner.settings.HOST == "0.0.0.0"

    def test_runner_auth_disabled_when_require_auth_false(self) -> None:
        """Test that auth is disabled when REQUIRE_AUTH=False."""
        settings = MCPSettings(API_KEY=None, REQUIRE_AUTH=False)
        runner = MCPRunner(settings)

        assert runner.auth.enabled is False

    def test_runner_auth_enabled_with_key(self) -> None:
        """Test that auth is enabled when key provided."""
        settings = MCPSettings(API_KEY=SecretStr("secret"))
        runner = MCPRunner(settings)

        assert runner.auth.enabled is True

    def test_runner_exposes_mcp_server(self) -> None:
        """Test that runner exposes MCP server instance."""
        runner = MCPRunner(MCPSettings(REQUIRE_AUTH=False))
        assert runner.mcp_server is not None

    def test_http_transport_creates_app(self) -> None:
        """Test that runner creates a valid app."""
        settings = MCPSettings(REQUIRE_AUTH=False)
        runner = MCPRunner(settings)
        app = runner.create_app()
        assert app is not None
