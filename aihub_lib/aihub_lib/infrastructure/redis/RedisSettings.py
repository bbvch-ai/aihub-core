from typing import Annotated

from pydantic import Field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class RedisSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("REDIS_")

    URL: Annotated[str, Field(description="Connection URL for Redis server")]
