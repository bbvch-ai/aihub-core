from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class NatsSettings(BaseSettings):
    NATS_NATS_IMAGE_TAG: Optional[str] = Field(..., description="image tag for nat image")
    NATS_REDIS_IMAGE_TAG: Optional[str] = Field(..., description="image tag for redis image")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )
