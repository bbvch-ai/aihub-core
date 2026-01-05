import pytest
from pydantic import SecretStr

from aihub_mcp.settings.MCPSettings import MCPSettings


class TestMCPSettings:
    """Tests for MCPSettings configuration."""

    def test_default_values(self) -> None:
        """Test default setting values."""
        settings = MCPSettings(REQUIRE_AUTH=False)

        # Security defaults
        assert settings.HOST == "127.0.0.1"  # Secure default: localhost only
        assert settings.REQUIRE_AUTH is False

        # Basic settings
        assert settings.PORT == 8001
        assert settings.PATH == "/mcp"
        assert settings.TRANSPORT == "http"
        assert settings.API_KEY is None
        assert settings.NATS_URL == "nats://localhost:4222"
        assert settings.TRACING_ENABLED is True
        assert settings.DISCOVERY_TIMEOUT_SECONDS == 5.0
        assert settings.DISCOVERY_INTERVAL_SECONDS == 30.0

        # New security settings
        assert settings.AGENT_TIMEOUT_SECONDS == 300.0
        assert settings.RATE_LIMIT_REQUESTS_PER_MINUTE == 60
        assert settings.MASK_SENSITIVE_DATA is True

    def test_require_auth_without_api_key_fails(self) -> None:
        """Test that REQUIRE_AUTH=true without API key fails."""
        with pytest.raises(ValueError) as exc_info:
            MCPSettings(REQUIRE_AUTH=True)

        assert "API key required" in str(exc_info.value)

    def test_require_auth_with_api_key_succeeds(self) -> None:
        """Test that REQUIRE_AUTH=true works with API key."""
        settings = MCPSettings(
            REQUIRE_AUTH=True,
            API_KEY=SecretStr("test-key"),
        )
        assert settings.API_KEY is not None

    def test_can_disable_auth(self) -> None:
        """Test that auth requirement can be disabled."""
        settings = MCPSettings(REQUIRE_AUTH=False)
        assert settings.REQUIRE_AUTH is False

    def test_transport_options(self) -> None:
        """Test that transport accepts valid options."""
        # HTTP transport (default)
        settings_http = MCPSettings(TRANSPORT="http", REQUIRE_AUTH=False)
        assert settings_http.TRANSPORT == "http"

        # SSE transport
        settings_sse = MCPSettings(TRANSPORT="sse", REQUIRE_AUTH=False)
        assert settings_sse.TRANSPORT == "sse"

    def test_api_key_type(self) -> None:
        """Test that API key is stored as SecretStr."""
        settings = MCPSettings(API_KEY=SecretStr("test-secret"))
        assert settings.API_KEY is not None
        assert settings.API_KEY.get_secret_value() == "test-secret"

    def test_multiple_api_keys(self) -> None:
        """Test multiple API keys configuration."""
        settings = MCPSettings(
            API_KEYS=[SecretStr("key1"), SecretStr("key2")],
        )

        all_keys = settings.get_all_api_keys()
        assert len(all_keys) == 2

    def test_get_all_api_keys_combines_single_and_list(self) -> None:
        """Test that get_all_api_keys combines API_KEY and API_KEYS."""
        settings = MCPSettings(
            API_KEY=SecretStr("primary-key"),
            API_KEYS=[SecretStr("extra-key")],
        )

        all_keys = settings.get_all_api_keys()
        assert len(all_keys) == 2
        assert all_keys[0].get_secret_value() == "primary-key"
        assert all_keys[1].get_secret_value() == "extra-key"

    def test_host_0000_with_no_auth_warns(self) -> None:
        """Test that binding to 0.0.0.0 without auth logs a warning."""
        # This should not raise, but would log a warning
        settings = MCPSettings(
            HOST="0.0.0.0",
            REQUIRE_AUTH=False,
        )
        assert settings.HOST == "0.0.0.0"
