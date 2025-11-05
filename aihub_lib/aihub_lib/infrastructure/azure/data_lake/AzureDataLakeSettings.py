from typing import Annotated

from pydantic import Field, SecretStr

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class AzureDataLakeSettings(EnvironmentSettings):
    """
    Configuration for connecting to Azure Data Lake Storage.

    Authentication priority:
    1. CONNECTION_STRING - if provided, uses explicit connection string authentication
    2. ENDPOINT + (implicit DefaultAzureCredential - DEPRECATED, will be removed)
    """

    model_config = EnvironmentSettings.create_settings_config("AZURE_DATA_LAKE_")

    CONNECTION_STRING: Annotated[
        SecretStr | None,
        Field(
            description="Azure Data Lake connection string for explicit authentication. "
            "Recommended over implicit authentication."
        ),
    ] = None
    NAME: Annotated[str, Field(description="Overwrite the datalake name")]
    ENDPOINT: Annotated[str, Field(description="Overwrite the datalake API endpoint")]
