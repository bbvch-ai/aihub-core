from typing import Annotated, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class OpenaiResourceSettings(BaseSettings):
    OPENAI_API_KEY: Annotated[Optional[str], Field(description="Azure OpenAI API Key", pattern="^[A-Za-z0-9]+$")] = None
