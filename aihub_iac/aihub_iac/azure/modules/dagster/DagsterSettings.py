from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DagsterSettings(BaseSettings):
    DAGSTER_IMAGE_TAG: Annotated[str | None, Field(description="-")] = None
    DAGSTER_OAUTH2_PROXY_COOKIE_SECRET: Annotated[str | None, Field(description="-")] = None
    DAGSTER_OAUTH2_PROXY_CLIENT_SECRET: Annotated[str | None, Field(description="-")] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )
