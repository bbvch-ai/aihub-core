from typing import Optional

from pydantic import Field
from pydantic_settings import SettingsConfigDict, BaseSettings


class PhoenixSettings(BaseSettings):
    PHOENIX_CLIENT_SECRET: Optional[str] = Field(default=None, description="-")
    PHOENIX_SECRET: Optional[str] = Field(default=None, description="-")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )
