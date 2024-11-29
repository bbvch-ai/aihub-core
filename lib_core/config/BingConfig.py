from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BingConfig(BaseSettings):
    BING_API_KEY: str = Field(..., description="API key for Bing")

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"), env_file_encoding="utf-8", extra="ignore"
    )
