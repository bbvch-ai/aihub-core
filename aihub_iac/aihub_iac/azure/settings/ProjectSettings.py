from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

from aihub_iac.azure.settings.utils import find_shared_env_file


class ProjectSettings(BaseSettings):
    APP_NAME: str = Field(..., description="name of the app")
    LOCATION: str = Field(..., description="location full name (e.g. Switzerland North)")
    LOCATION_SHORT: str = Field(..., description="location short name (e.g. sui)")
    RESOURCE_GROUP: str = Field(..., description="resource group name")
    ARM_SUBSCRIPTION_ID: str = Field(..., description="subscription id")

    model_config = SettingsConfigDict(
        env_file=[find_shared_env_file(), ".env"],
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )
