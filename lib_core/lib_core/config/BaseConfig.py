from pathlib import Path
from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    AZURE_SUBSCRIPTION_NAME: str = Field(
        ...,
        pattern=r"^sub-lz-[\w-]+-[\w-]+-\d{3}$",
        description="Azure subscription name",
    )
    ENVIRONMENT: Literal["dev", "prod"] = Field(
        ..., description="Environment: dev or prod"
    )
    APP_NAME: str = Field(
        ..., pattern=r"^[a-z]+$", description="App name: lowercase, no whitespace"
    )
    REGION_SHORT: str = Field(
        ..., min_length=2, max_length=3, description="ISO country code"
    )

    SHARED_DB_NAME: str = Field(
        "SHARED",
        pattern=r"^[A-Z]+$",
        description="Database holding collections that are shared between all organizations in the DB cluster",
    )

    DEV_DEBUG: bool = Field(False, description="Debug mode for development")
    VERSION: Optional[str] = Field(None, description="Version of the app")

    FRONTEND_ORIGIN: Optional[str] = Field(
        None, description="Comma separated list of origins to allow CORS"
    )

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )
