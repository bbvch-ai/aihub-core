from typing import Annotated
from urllib.parse import urlparse, urlunparse

from pydantic import Field, SecretStr

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class RedisSettings(EnvironmentSettings):
    """Settings for Redis/Valkey connection with optional password authentication."""

    model_config = EnvironmentSettings.create_settings_config("REDIS_")

    URL: Annotated[str, Field(description="Connection URL for Redis server (without password)")]
    PASSWORD: Annotated[
        SecretStr | None,
        Field(default=None, description="Authentication password for Redis server. If not set, no auth is used."),
    ]

    def get_connection_url(self) -> str:
        """
        Build Redis connection URL with embedded password if configured.

        Returns URL in format: redis://default:password@host:port or redis://host:port
        """
        if self.PASSWORD is None:
            return self.URL

        # Parse URL and inject password
        parsed = urlparse(self.URL)
        password = self.PASSWORD.get_secret_value()

        # Build new URL with password (using 'default' as username for Redis)
        netloc = f"default:{password}@{parsed.hostname}"
        if parsed.port:
            netloc += f":{parsed.port}"

        return urlunparse((parsed.scheme, netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
