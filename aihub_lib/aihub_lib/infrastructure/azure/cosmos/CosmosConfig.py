from typing import Annotated, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CosmosConfig(BaseSettings):
    COSMOS_CONNECTION_STRING: Annotated[Optional[str], Field(description="Overwrite the MongoDB connection string")] = (
        None
    )
    COSMOS_RESOURCE_GROUP_NAME: Annotated[
        Optional[str], Field(description="Overwrite the MongoDB resource group name")
    ] = None
    COSMOS_ACCOUNT_NAME: Annotated[Optional[str], Field(description="Overwrite the MongoDB account name")] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
