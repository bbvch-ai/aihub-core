from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SpeechServiceConfig(BaseSettings):
    SPEECH_SERVICE_KEY: Annotated[str | None, Field(description="Key for Speech Service")] = None
    SPEECH_SERVICE_REGION: Annotated[str | None, Field(description="Region for Speech Service")] = None
    SPEECH_SERVICE_RESOURCE_GROUP_NAME: Annotated[
        str | None, Field(description="Resource Group Name of the Speech Service")
    ] = None
    SPEECH_SERVICE_NAME: Annotated[str | None, Field(description="Name of the Speech Service Resource")] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
