from typing import Annotated, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AISearchConfig(BaseSettings):
    COGNITIVE_SEARCH_RESOURCE_GROUP_NAME: Annotated[
        Optional[str], Field(description="Overwrite the cognitive search resource group")
    ] = None
    COGNITIVE_SEARCH_NAME: Annotated[
        Optional[str], Field(description="Overwrite the cognitive search service name")
    ] = None
    COGNITIVE_SEARCH_ENDPOINT: Annotated[
        Optional[str], Field(description="Overwrite the cognitive search API endpoint")
    ] = None
    COGNITIVE_SEARCH_API_KEY: Annotated[Optional[str], Field(description="Overwrite the cognitive search API key")] = (
        None
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
