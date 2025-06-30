from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GeminiConfig(BaseSettings):
    GOOGLE_GEMINI_API_KEY: Annotated[str, Field(description="Google gemini API key")]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
