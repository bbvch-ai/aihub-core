from typing import Annotated

from nats.aio.client import Client as NATS
from pydantic import Field, SecretStr

from swiss_ai_hub.core.settings.environment_settings import EnvironmentSettings


class NatsSettings(EnvironmentSettings):
    """Settings for NATS messaging system connection with optional token authentication."""

    model_config = EnvironmentSettings.create_settings_config("NATS_")

    ENDPOINT: Annotated[str, Field(description="Connection endpoint for NATS messaging system")]
    TOKEN: Annotated[
        SecretStr | None,
        Field(default=None, description="Authentication token for NATS server. If not set, no auth is used."),
    ]

    @classmethod
    async def create_client(cls) -> NATS:
        """
        Create and connect a NATS client with settings from environment variables.

        Returns a connected NATS client instance configured with the endpoint and optional token
        authentication from the environment settings.

        Example:
            nc = await NatsSettings.create_client()
            # Use nc for NATS operations
            await nc.close()
        """
        settings = cls()
        nc = NATS()
        servers = [settings.ENDPOINT]
        token = settings.TOKEN.get_secret_value() if settings.TOKEN else None
        await nc.connect(servers=servers, token=token)
        return nc
