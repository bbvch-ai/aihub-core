from typing import Annotated, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PhoenixSettings(BaseSettings):
    PHOENIX_CLIENT_SECRET: Annotated[Optional[str], Field(description="-")] = None
    PHOENIX_SECRET: Annotated[Optional[str], Field(description="-")] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )
