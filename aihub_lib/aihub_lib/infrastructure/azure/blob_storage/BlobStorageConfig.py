from typing import Annotated, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BlobStorageConfig(BaseSettings):
    """
    Configuration for connecting to Azure Blob Storage.
    Reads settings from environment variables or a .env file.
    """

    BLOB_STORAGE_NAME: Annotated[Optional[str], Field(description="The name of the Azure Blob Storage account.")] = None
    BLOB_STORAGE_ENDPOINT: Annotated[
        Optional[str], Field(description="The Blob service endpoint for the storage account.")
    ] = None

    # This secret key is used to sign our own internal URLs, not for Azure.
    URL_SIGNING_SECRET: Annotated[
        str,
        Field(
            description="A secret key used for signing and verifying temporary anonymous access URLs.",
        ),
    ] = "change-this-super-secret-key-in-production"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
