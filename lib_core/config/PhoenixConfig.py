from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class PhoenixConfig(BaseSettings):
    PHOENIX_ENDPOINT: str = Field(..., pattern=r"^https?://.*$")
    PHOENIX_USERNAME: str = Field(..., description="Username for Phoenix")
    PHOENIX_PASSWORD: str = Field(..., description="Password for Phoenix")

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"), env_file_encoding="utf-8", extra="ignore"
    )
