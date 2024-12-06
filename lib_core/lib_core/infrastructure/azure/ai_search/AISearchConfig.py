from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AISearchConfig(BaseSettings):
    COGNITIVE_SEARCH_RESOURCE_GROUP_NAME: Optional[str] = Field(
        None, description="Overwrite the cognitive search resource group"
    )
    COGNITIVE_SEARCH_NAME: Optional[str] = Field(
        None, description="Overwrite the cognitive search service name"
    )
    COGNITIVE_SEARCH_ENDPOINT: Optional[str] = Field(
        None, description="Overwrite the cognitive search API endpoint"
    )
    COGNITIVE_SEARCH_API_KEY: Optional[str] = Field(
        None, description="Overwrite the cognitive search API key"
    )

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )
