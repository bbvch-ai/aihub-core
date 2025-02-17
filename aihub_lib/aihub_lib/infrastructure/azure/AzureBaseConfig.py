from typing import Literal, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AzureBaseConfig(BaseSettings):
    AZURE_SUBSCRIPTION_NAME: str = Field(
        ...,
        pattern=r"^sub-lz-[\w-]+-[\w-]+-\d{3}$",
        description="Azure subscription name",
    )
    ENVIRONMENT: Literal["dev", "prod"] = Field(..., description="Environment: dev or prod")
    APP_NAME: str = Field(..., pattern=r"^[a-z]+$", description="App name: lowercase, no whitespace")
    REGION_SHORT: str = Field(..., min_length=2, max_length=3, description="ISO country code")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
