from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatalakeConfig(BaseSettings):
    DATA_LAKE_NAME: Optional[str] = Field(
        None, description="Overwrite the datalake name"
    )
    DATA_LAKE_ENDPOINT: Optional[str] = Field(
        None, description="Overwrite the datalake API endpoint"
    )

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )
