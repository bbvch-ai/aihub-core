"""Tests for MCP settings."""


from aihub_mcp.settings.MCPSettings import MCPSettings


class TestMCPSettings:
    """Tests for MCPSettings configuration."""

    def test_default_values(self) -> None:
        """Test default setting values."""
        settings = MCPSettings()

        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8001
        assert settings.PATH == "/mcp"
        assert settings.TRANSPORT == "http"
        assert settings.API_KEY is None
        assert settings.NATS_URL == "nats://localhost:4222"
        assert settings.TRACING_ENABLED is True
        assert settings.DISCOVERY_TIMEOUT_SECONDS == 5.0
        assert settings.DISCOVERY_INTERVAL_SECONDS == 30.0
        assert settings.DEBUG is False

    def test_transport_options(self) -> None:
        """Test that transport accepts valid options."""
        # HTTP transport (default)
        settings_http = MCPSettings(TRANSPORT="http")
        assert settings_http.TRANSPORT == "http"

        # SSE transport
        settings_sse = MCPSettings(TRANSPORT="sse")
        assert settings_sse.TRANSPORT == "sse"

    def test_api_key_type(self) -> None:
        """Test that API key is stored as SecretStr."""
        from pydantic import SecretStr

        settings = MCPSettings(API_KEY=SecretStr("test-secret"))  # type: ignore
        assert settings.API_KEY is not None
        assert settings.API_KEY.get_secret_value() == "test-secret"
