from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings


class BotRunnerSettings(BaseSettings):
    MODEL_URL: Annotated[str, Field(description="Model SUI URL", pattern="^https?://.+$")] = "https://api.example.com"
    MODEL_API_KEY: Annotated[str | None, Field(description="Azure OpenAI API Key", pattern="^[A-Za-z0-9]+$")] = None
