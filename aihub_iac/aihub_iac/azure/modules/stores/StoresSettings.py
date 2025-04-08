from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class StoresSettings(BaseSettings):
    STORES_POSTGRES_USERNAME: Optional[str] = Field(..., description="username for postgres")
    STORES_POSTGRES_PASSWORD: Optional[str] = Field(..., description="password for postgres")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )
