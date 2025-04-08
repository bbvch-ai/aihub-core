from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class RegistrySettings(BaseSettings):
    REGISTRY_USER: str = Field(..., description="registry username")
    REGISTRY_PAT: str = Field(..., description="registry personal access token")
    REGISTRY_URL: str = Field(default="https://ghcr.io", description="registry personal access token")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )
