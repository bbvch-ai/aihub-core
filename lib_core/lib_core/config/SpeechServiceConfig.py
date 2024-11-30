from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SpeechServiceConfig(BaseSettings):
    SPEECH_SERVICE_KEY: Optional[str] = Field(None, description="Key for Speech Service")
    SPEECH_SERVICE_REGION: Optional[str] = Field(None, description="Region for Speech Service")
    SPEECH_SERVICE_RESOURCE_GROUP_NAME: Optional[str] = Field(
        None, description="Resource Group Name of the Speech Service"
    )
    SPEECH_SERVICE_NAME: Optional[str] = Field(None, description="Name of the Speech Service Resource")

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"), env_file_encoding="utf-8", extra="ignore"
    )
