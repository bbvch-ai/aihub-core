from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from aihub_iac.azure.settings.utils import find_shared_env_file


class OAuthSettings(BaseSettings):
    CLIENT_ID: Annotated[str, Field(description="client id")]
    TENANT_ID: Annotated[str, Field(description="tenant id")]
    AUTHORITY_URL: Annotated[str, Field(description="authority url")]

    model_config = SettingsConfigDict(
        env_file=[find_shared_env_file(), ".env"],
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )
