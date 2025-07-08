from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiConfig(BaseSettings):
    DEV_DEBUG: Annotated[bool, Field(description="Debug mode for development")] = False
    VERSION: Annotated[str | None, Field(description="Version of the app")] = None

    FRONTEND_ORIGIN: Annotated[str | None, Field(description="Comma separated list of origins to allow CORS")] = None

    DB_NAME: Annotated[
        str,
        Field(
            pattern=r"^[A-Za-z]+$",
            description="Database holding collections that are shared between all organizations in the DB cluster",
        ),
    ] = "aihub"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
