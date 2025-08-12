from typing import Annotated

from pydantic import Field, SecretStr

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class AzureAISearchSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("AZURE_AI_SEARCH_")

    RESOURCE_GROUP_NAME: Annotated[str | None, Field(description="Overwrite the cognitive search resource group")] = (
        None
    )
    NAME: Annotated[str | None, Field(description="Overwrite the cognitive search service name")] = None
    ENDPOINT: Annotated[str | None, Field(description="Overwrite the cognitive search API endpoint")] = None
    API_KEY: Annotated[SecretStr | None, Field(description="Overwrite the cognitive search API key")] = None
