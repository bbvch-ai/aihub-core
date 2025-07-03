from typing import Annotated, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DataLakeConfig(BaseSettings):
    DATA_LAKE_NAME: Annotated[Optional[str], Field(description="Overwrite the datalake name")] = None
    DATA_LAKE_ENDPOINT: Annotated[Optional[str], Field(description="Overwrite the datalake API endpoint")] = None
    DATA_LAKE_ACCOUNT_KEY: Annotated[
        Optional[str],
        Field(
            description="Allows authentication towards the Data Lake using an account key instead of implicit az login",
        ),
    ] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
