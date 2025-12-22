from typing import Annotated

from pydantic import Field, SecretStr

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class NatsSettings(EnvironmentSettings):
    """Settings for NATS messaging system connection with optional token authentication."""

    model_config = EnvironmentSettings.create_settings_config("NATS_")

    ENDPOINT: Annotated[str, Field(description="Connection endpoint for NATS messaging system")]
    TOKEN: Annotated[
        SecretStr | None,
        Field(default=None, description="Authentication token for NATS server. If not set, no auth is used."),
    ]

    def get_connection_url(self) -> str:
        """
        Build NATS connection URL with embedded token if configured.

        Returns URL in format: nats://token@host:port or nats://host:port
        """
        if self.TOKEN is None:
            return self.ENDPOINT

        # Parse endpoint and inject token
        # Expected format: nats://host:port
        token = self.TOKEN.get_secret_value()
        if self.ENDPOINT.startswith("nats://"):
            return f"nats://{token}@{self.ENDPOINT[7:]}"
        return self.ENDPOINT
