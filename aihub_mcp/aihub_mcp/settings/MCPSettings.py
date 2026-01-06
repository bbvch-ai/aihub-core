import logging
from typing import Annotated, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class MCPSettings(BaseSettings):
    """
    Configuration for the MCP server.

    All settings can be configured via environment variables with the MCP_ prefix,
    or via a .env file. Infrastructure settings (NATS, Redis) use shared lib settings.
    """

    model_config = SettingsConfigDict(
        env_prefix="MCP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server configuration
    HOST: Annotated[str, Field(
        default="127.0.0.1",
        description="Host to bind. Use 0.0.0.0 for network access.",
    )]
    PORT: Annotated[int, Field(
        default=8001,
        description="Port to bind",
    )]

    # Authentication
    API_KEY: Annotated[SecretStr | None, Field(
        default=None,
        description="API key for authentication. Required when REQUIRE_AUTH=true.",
    )]
    REQUIRE_AUTH: Annotated[bool, Field(
        default=True,
        description="Require API key authentication.",
    )]

    @model_validator(mode="after")
    def validate_security_settings(self) -> Self:
        """Ensure API key is configured when authentication is required."""
        if self.REQUIRE_AUTH and self.API_KEY is None:
            raise ValueError("API key required. Set MCP_API_KEY or set MCP_REQUIRE_AUTH=false to disable.")

        if self.HOST == "0.0.0.0" and self.API_KEY is None:
            logger.warning("Server bound to 0.0.0.0 without authentication. This is a security risk!")

        return self
