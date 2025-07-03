from typing import Annotated, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PhoenixConfig(BaseSettings):
    PHOENIX_ENDPOINT: Annotated[str, Field(pattern=r"^https?://.*$")] = "http://localhost:6006"
    PHOENIX_AUTH_TOKEN: Annotated[Optional[str], Field(description="Phoenix API Token")] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
