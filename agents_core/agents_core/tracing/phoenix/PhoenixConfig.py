from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PhoenixConfig(BaseSettings):
    PHOENIX_ENDPOINT: str = Field("http://localhost:6006", pattern=r"^https?://.*$")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
