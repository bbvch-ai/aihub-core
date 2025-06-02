from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CeleryConfig(BaseSettings):
    CELERY_BROKER: str = Field("redis://localhost:6389/0")
    CELERY_BACKEND: str = Field("redis://localhost:6389/1")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
