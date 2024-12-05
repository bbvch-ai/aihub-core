from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AvatarConfig(BaseSettings):
    DID_CLIENT_KEY: str = Field(..., description="Key for D-ID Client")
    DID_AGENT_ID: str = Field(..., description="Agent ID for D-ID")

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )
