"""Configuration settings for the MCP server."""

from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPSettings(BaseSettings):
    """
    Configuration for the MCP server.

    All settings can be configured via environment variables with the MCP_ prefix,
    or via a .env file.
    """

    model_config = SettingsConfigDict(
        env_prefix="MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server configuration
    HOST: str = Field(
        default="0.0.0.0",
        description="Host address to bind the MCP server",
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
        description="API key for authenticating MCP clients. If None, authentication is disabled.",
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

    # Server behavior
    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode with verbose logging",
    )
