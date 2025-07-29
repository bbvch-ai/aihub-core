from typing import Annotated, ClassVar

from pydantic import Field
from pydantic_settings import BaseSettings

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class BotRunnerSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("BOT_")

    MODEL_URL: Annotated[str, Field(description="Model SUI URL", pattern="^https?://.+$")]
    MODEL_API_KEY: Annotated[str | None, Field(description="Azure OpenAI API Key", pattern="^[A-Za-z0-9]+$")] = None
