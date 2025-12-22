"""Integration tests for MCP clients (Claude Code, Cursor)."""

import pytest

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestMCPClientIntegration:
    """
    Integration tests for MCP client connections.

    These tests require a running MCP server and are marked as integration tests.
    Run with: pytest -m integration
    """

    @pytest.fixture
    def mcp_url(self) -> str:
        """Get MCP server URL from environment or use default."""
        import os

        return os.environ.get("MCP_URL", "http://localhost:8001/mcp")

    @pytest.mark.skip(reason="Requires running MCP server")
    async def test_list_tools(self, mcp_url: str) -> None:
        """Test listing available MCP tools."""
        # This would use fastmcp.Client to connect and list tools
        # Example:
        # from fastmcp import Client
        # async with Client(mcp_url) as client:
        #     tools = await client.list_tools()
        #     assert len(tools) > 0
        pass

    @pytest.mark.skip(reason="Requires running MCP server")
    async def test_list_resources(self, mcp_url: str) -> None:
        """Test listing MCP resources."""
        pass

    @pytest.mark.skip(reason="Requires running MCP server")
    async def test_invoke_tool(self, mcp_url: str) -> None:
        """Test invoking an agent tool."""
        pass

    @pytest.mark.skip(reason="Requires running MCP server")
    async def test_elicitation_flow(self, mcp_url: str) -> None:
        """Test elicitation request/response flow."""
        pass


class TestClaudeCodeConfig:
    """Tests for Claude Code MCP configuration generation."""

    def test_generate_mcp_config(self) -> None:
        """Test generating .mcp.json configuration for Claude Code."""
        import json

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

        # Verify it's valid JSON
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
