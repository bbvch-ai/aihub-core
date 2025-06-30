from typing import Annotated, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingConfig(BaseSettings):
    LOG_LEVEL: Annotated[
        Optional[str | int], Field(description="Logging level (can be string like 'INFO' or integer)")
    ] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
