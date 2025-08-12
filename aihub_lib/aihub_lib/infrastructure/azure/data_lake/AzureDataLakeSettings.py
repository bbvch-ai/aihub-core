from typing import Annotated

from pydantic import Field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class AzureDataLakeSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("AZURE_DATA_LAKE_")

    NAME: Annotated[str, Field(description="Overwrite the datalake name")]
    ENDPOINT: Annotated[str, Field(description="Overwrite the datalake API endpoint")]
