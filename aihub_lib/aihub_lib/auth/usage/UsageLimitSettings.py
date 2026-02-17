from typing import Annotated

from pydantic import Field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class UsageLimitSettings(EnvironmentSettings):
    """Configurable settings for usage limit behavior."""

    model_config = EnvironmentSettings.create_settings_config("USAGE_LIMIT_")

    WARNING_THRESHOLD_PERCENT: Annotated[
        int,
        Field(ge=0, le=100, description="Usage percentage at which warning headers are emitted"),
    ] = 80
