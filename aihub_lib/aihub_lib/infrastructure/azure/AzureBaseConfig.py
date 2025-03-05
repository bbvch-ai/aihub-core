from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AzureBaseConfig(BaseSettings):
    AZURE_SUBSCRIPTION_ID: str = Field(
        ...,
        pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
        description="Azure subscription id (GUID format)",
    )
    APP_NAME: str = Field(..., pattern=r"^[a-z-]+$", description="App name: lowercase, no whitespace")
    REGION_SHORT: str = Field(..., min_length=2, max_length=3, description="ISO country code")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
