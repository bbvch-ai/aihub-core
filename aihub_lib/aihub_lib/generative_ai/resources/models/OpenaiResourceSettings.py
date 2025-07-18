from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings


class OpenaiResourceSettings(BaseSettings):
    OPENAI_API_KEY: Annotated[str | None, Field(description="Azure OpenAI API Key", pattern="^[A-Za-z0-9]+$")] = None
