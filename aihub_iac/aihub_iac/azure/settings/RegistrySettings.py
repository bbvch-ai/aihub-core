from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from aihub_iac.azure.settings.utils import find_shared_env_file


class RegistrySettings(BaseSettings):
    REGISTRY_USER: Annotated[str, Field(description="registry username")]
    REGISTRY_PAT: Annotated[str, Field(description="registry personal access token")]
    REGISTRY_URL: Annotated[str, Field(description="registry personal access token")] = "ghcr.io"

    model_config = SettingsConfigDict(
        env_file=[find_shared_env_file(), ".env"],
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )
