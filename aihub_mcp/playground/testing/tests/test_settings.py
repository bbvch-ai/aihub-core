import pytest
from pydantic import SecretStr

from aihub_mcp.settings.MCPSettings import MCPSettings


class TestMCPSettings:
    """Tests for MCPSettings configuration."""

    def test_default_values(self) -> None:
        """Test default setting values."""
        settings = MCPSettings(REQUIRE_AUTH=False)

        assert settings.HOST == "127.0.0.1"
        assert settings.PORT == 8001
        assert settings.API_KEY is None
        assert settings.REQUIRE_AUTH is False
        assert settings.NATS_URL == "nats://localhost:4222"
        assert settings.REDIS_URL == "redis://localhost:6379"

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

    def test_api_key_type(self) -> None:
        """Test that API key is stored as SecretStr."""
        settings = MCPSettings(API_KEY=SecretStr("test-secret"))
        assert settings.API_KEY is not None
        assert settings.API_KEY.get_secret_value() == "test-secret"
