from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AzureInstrumentationConfig(BaseSettings):
    AZURE_INSTRUMENTATION_KEY: Optional[str] = Field(None, description="Azure instrumentation key")

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"), env_file_encoding="utf-8", extra="ignore"
    )
