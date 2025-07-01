from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresAuthSettings(BaseSettings):
    POSTGRES_USERNAME: Annotated[str, Field(description="Username for PostgreSQL database authentication")]
    POSTGRES_PASSWORD: Annotated[str, Field(description="Password for PostgreSQL database authentication")]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )
