import logging
from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class MCPSettings(BaseSettings):
    """
    Configuration for the MCP server.

    All settings can be configured via environment variables with the MCP_ prefix,
    or via a .env file.

    Security notes:
    - API_KEY is required when REQUIRE_AUTH=true (default)
    - HOST defaults to 127.0.0.1 for security; set to 0.0.0.0 for network access
    """

    model_config = SettingsConfigDict(
        env_prefix="MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server configuration
    HOST: str = Field(
        default="127.0.0.1",
        description="Host address to bind the MCP server. Use 0.0.0.0 for network access.",
    )
    PORT: int = Field(
        default=8001,
        description="Port to bind the MCP server",
    )
    PATH: str = Field(
        default="/mcp",
        description="URL path for the MCP endpoint",
    )
    TRANSPORT: Literal["http", "sse"] = Field(
        default="http",
        description="Transport type: 'http' for Streamable HTTP (recommended), 'sse' for Server-Sent Events",
    )

    # Authentication
    API_KEY: SecretStr | None = Field(
        default=None,
        description="API key for authenticating MCP clients. Required when REQUIRE_AUTH=true.",
    )
    API_KEYS: list[SecretStr] = Field(
        default_factory=list,
        description="Additional API keys for multiple clients. Each can be mapped to a user identity.",
    )
    REQUIRE_AUTH: bool = Field(
        default=True,
        description="Require API key authentication for MCP clients.",
    )

    # NATS configuration
    NATS_URL: str = Field(
        default="nats://localhost:4222",
        description="NATS server URL for Swiss AI Agent Protocol communication",
    )

    # Tracing configuration
    TRACING_ENABLED: bool = Field(
        default=True,
        description="Enable OpenTelemetry tracing for MCP requests",
    )

    # Agent discovery
    DISCOVERY_TIMEOUT_SECONDS: float = Field(
        default=5.0,
        description="Timeout for agent discovery requests",
    )
    DISCOVERY_INTERVAL_SECONDS: float = Field(
        default=30.0,
        description="Interval between agent discovery refreshes",
    )

    # Agent execution
    AGENT_TIMEOUT_SECONDS: float = Field(
        default=300.0,
        description="Maximum time to wait for agent execution (5 minutes default)",
    )

    # Rate limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(
        default=60,
        description="Maximum requests per minute per client. 0 to disable.",
    )

    # Logging security
    MASK_SENSITIVE_DATA: bool = Field(
        default=True,
        description="Mask potentially sensitive data in logs",
    )

    @model_validator(mode="after")
    def validate_security_settings(self) -> Self:
        """Validate security configuration based on environment."""
        has_api_keys = self.API_KEY is not None or len(self.API_KEYS) > 0

        if self.REQUIRE_AUTH and not has_api_keys:
            raise ValueError(
                "API key required. " "Set MCP_API_KEY or MCP_API_KEYS, or set MCP_REQUIRE_AUTH=false to disable."
            )

        if self.HOST == "0.0.0.0" and not has_api_keys:
            logger.warning("Server bound to all interfaces (0.0.0.0) without authentication. This is a security risk!")

        return self

    def get_all_api_keys(self) -> list[SecretStr]:
        """Get all configured API keys."""
        keys = list(self.API_KEYS)
        if self.API_KEY:
            keys.insert(0, self.API_KEY)
        return keys
