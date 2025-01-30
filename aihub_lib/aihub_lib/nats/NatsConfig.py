from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class NatsConfig(BaseSettings):
    NATS_ENDPOINT: str = Field("nats://localhost:4222")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
