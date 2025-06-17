from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BlobStorageConfig(BaseSettings):
    """
    Configuration for connecting to Azure Blob Storage.
    Reads settings from environment variables or a .env file.
    """

    BLOB_STORAGE_NAME: Optional[str] = Field(None, description="The name of the Azure Blob Storage account.")
    BLOB_STORAGE_ENDPOINT: Optional[str] = Field(None, description="The Blob service endpoint for the storage account.")

    # This secret key is used to sign our own internal URLs, not for Azure.
    URL_SIGNING_SECRET: str = Field(
        "change-this-super-secret-key-in-production",
        description="A secret key used for signing and verifying temporary anonymous access URLs.",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
