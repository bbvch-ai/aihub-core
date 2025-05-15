from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DataLakeConfig(BaseSettings):
    DATA_LAKE_NAME: Optional[str] = Field(None, description="Overwrite the datalake name")
    DATA_LAKE_ENDPOINT: Optional[str] = Field(None, description="Overwrite the datalake API endpoint")
    DATA_LAKE_ACCOUNT_KEY: Optional[str] = Field(None, description="Storage account key for authentication")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
