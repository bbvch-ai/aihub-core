from typing import Annotated

from pydantic import Field, SecretStr

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class AzureBlobStorageSettings(EnvironmentSettings):
    """
    Configuration for connecting to Azure Blob Storage.
    Reads settings from environment variables or a .env file.

    Authentication priority:
    1. CONNECTION_STRING - if provided, uses explicit connection string authentication
    2. ENDPOINT + (implicit DefaultAzureCredential - DEPRECATED, will be removed)
    """

    model_config = EnvironmentSettings.create_settings_config("AZURE_BLOB_STORAGE_")

    CONNECTION_STRING: Annotated[
        SecretStr | None,
        Field(
            description="Azure Blob Storage connection string for explicit authentication. "
            "Recommended over implicit authentication."
        ),
    ] = None

    # This secret key is used to sign our own internal URLs, not for Azure.
    URL_SIGNING_SECRET: Annotated[
        SecretStr,
        Field(
            description="A secret key used for signing and verifying temporary anonymous access URLs.",
        ),
    ]
