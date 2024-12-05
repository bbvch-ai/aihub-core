from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class WhisperConfig(BaseSettings):
    WHISPER_API_KEY: str = Field(..., description="API key for Whisper")
    WHISPER_API_VERSION: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    WHISPER_API_ENDPOINT: str = Field(..., pattern=r"^https?://.*$")

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )
