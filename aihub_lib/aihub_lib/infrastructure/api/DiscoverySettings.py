from typing import Annotated

from pydantic import Field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class DiscoverySettings(EnvironmentSettings):
    """Settings for agent/process discovery timeouts and caching."""

    model_config = EnvironmentSettings.create_settings_config("AIHUB_DISCOVERY_")

    CLASS_DISCOVERY_TIMEOUT: Annotated[
        float, Field(description="Timeout in seconds for agent/process class discovery via NATS")
    ] = 2.0

    INSTANCE_DISCOVERY_TIMEOUT: Annotated[
        float, Field(description="Timeout in seconds for agent/process instance discovery via NATS")
    ] = 2.0
