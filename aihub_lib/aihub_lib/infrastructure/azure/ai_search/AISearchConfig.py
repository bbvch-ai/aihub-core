from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AISearchConfig(BaseSettings):
    COGNITIVE_SEARCH_RESOURCE_GROUP_NAME: Annotated[
        str | None, Field(description="Overwrite the cognitive search resource group")
    ] = None
    COGNITIVE_SEARCH_NAME: Annotated[str | None, Field(description="Overwrite the cognitive search service name")] = (
        None
    )
    COGNITIVE_SEARCH_ENDPOINT: Annotated[
        str | None, Field(description="Overwrite the cognitive search API endpoint")
    ] = None
    COGNITIVE_SEARCH_API_KEY: Annotated[str | None, Field(description="Overwrite the cognitive search API key")] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
