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
