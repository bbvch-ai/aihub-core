from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class ApiConfig(BaseSettings):
    DEV_DEBUG: bool = Field(False, description="Debug mode for development")
    VERSION: Optional[str] = Field(None, description="Version of the app")

    FRONTEND_ORIGIN: Optional[str] = Field(None, description="Comma separated list of origins to allow CORS")

    DB_NAME: str = Field(
        "aihub",
        pattern=r"^[A-Za-z]+$",
        description="Database holding collections that are shared between all organizations in the DB cluster",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
