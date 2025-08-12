from typing import Annotated

from pydantic import Field, SecretStr

from aihub_lib.settings.EnvironmentSettings import EnvironmentSettings


class AzureSpeechServiceSettings(EnvironmentSettings):
    model_config = EnvironmentSettings.create_settings_config("AZURE_SPEECH_SERVICE_")

    KEY: Annotated[SecretStr | None, Field(description="Key for Speech Service")] = None
    REGION: Annotated[str | None, Field(description="Region for Speech Service")] = None
    GROUP_NAME: Annotated[str | None, Field(description="Resource Group Name of the Speech Service")] = None
    RESOURCE_NAME: Annotated[str | None, Field(description="Name of the Speech Service Resource")] = None
