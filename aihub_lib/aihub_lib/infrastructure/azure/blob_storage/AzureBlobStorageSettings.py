from typing import Annotated

from pydantic import Field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class AzureBlobStorageSettings(EnvironmentSettings):
    """
    Configuration for connecting to Azure Blob Storage.
    Reads settings from environment variables or a .env file.
    """

    model_config = EnvironmentSettings.create_settings_config("AZURE_BLOB_STORAGE_")

    NAME: Annotated[str | None, Field(description="The name of the Azure Blob Storage account.")] = None
    ENDPOINT: Annotated[str | None, Field(description="The Blob service endpoint for the storage account.")] = None

    # This secret key is used to sign our own internal URLs, not for Azure.
    URL_SIGNING_SECRET: Annotated[
        str,
        Field(
            description="A secret key used for signing and verifying temporary anonymous access URLs.",
        ),
    ]
