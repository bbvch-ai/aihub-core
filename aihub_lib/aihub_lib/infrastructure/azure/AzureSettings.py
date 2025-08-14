from typing import Annotated

from pydantic import Field

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class AzureSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("AZURE_")

    SUBSCRIPTION_ID: Annotated[
        str,
        Field(
            pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
            description="Azure subscription id (GUID format)",
        ),
    ]
    APP_NAME: Annotated[str, Field(pattern=r"^[a-z-]+$", description="App name: lowercase, no whitespace")]
    REGION_SHORT: Annotated[str, Field(min_length=2, max_length=3, description="ISO country code")]
