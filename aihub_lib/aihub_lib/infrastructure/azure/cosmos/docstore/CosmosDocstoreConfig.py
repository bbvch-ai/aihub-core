from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CosmosDocstoreConfig(BaseSettings):
    COSMOS_DOCSTORE_CONNECTION_STRING: Optional[str] = Field(
        None, description="Overwrite the MongoDB connection string"
    )
    COSMOS_DOCSTORE_RESOURCE_GROUP_NAME: Optional[str] = Field(
        None, description="Overwrite the MongoDB resource group name"
    )
    COSMOS_DOCSTORE_ACCOUNT_NAME: Optional[str] = Field(None, description="Overwrite the MongoDB account name")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
