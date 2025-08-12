from typing import Annotated

from pydantic import Field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class NatsSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("NATS_")

    ENDPOINT: Annotated[str, Field(description="Connection endpoint for NATS messaging system")]
