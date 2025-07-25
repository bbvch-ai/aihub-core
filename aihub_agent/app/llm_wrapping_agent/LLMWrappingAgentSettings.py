from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings


class LLMWrappingAgentSettings(BaseSettings):
    MODEL_SUI_URL: Annotated[str, Field(description="Model SUI URL", pattern="^https?://.+$")]
    MODEL_SUI_API_KEY: Annotated[str | None, Field(description="Azure OpenAI API Key", pattern="^[A-Za-z0-9]+$")] = None
    MODEL_NAME: Annotated[str, Field(description="Model name", pattern="^[A-Za-z0-9_-]+$")] = "gpt-4o"

    class Config:
        env_file = ".env"