from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DagsterSettings(BaseSettings):
    DAGSTER_IMAGE_TAG: Optional[str] = Field(default=None, description="-")
    DAGSTER_OAUTH2_PROXY_COOKIE_SECRET: Optional[str] = Field(default=None, description="-")
    DAGSTER_OAUTH2_PROXY_CLIENT_SECRET: Optional[str] = Field(default=None, description="-")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )
