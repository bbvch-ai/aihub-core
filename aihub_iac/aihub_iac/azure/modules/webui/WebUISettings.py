from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class WebUISettings(BaseSettings):
    WEBUI_REDIS_ENDPOINT: Optional[str] = Field(..., description="tbd")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )
