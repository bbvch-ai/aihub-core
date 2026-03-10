from typing import Annotated

from pydantic import Field, SecretStr

from swiss_ai_hub.core.settings.EnvironmentSettings import EnvironmentSettings


class AzureDataLakeSettings(EnvironmentSettings):
    """
    Configuration for connecting to Azure Data Lake Storage.

    Authentication priority:
    1. CONNECTION_STRING - if provided, uses explicit connection string authentication
    2. ENDPOINT + (implicit DefaultAzureCredential - DEPRECATED, will be removed)
    """

    model_config = EnvironmentSettings.create_settings_config("AZURE_DATA_LAKE_")

    CONNECTION_STRING: Annotated[
        SecretStr,
        Field(
            description="Azure Data Lake connection string for explicit authentication. "
            "Recommended over implicit authentication."
        ),
    ]
