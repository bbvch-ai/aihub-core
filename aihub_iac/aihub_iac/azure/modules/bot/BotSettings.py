from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class BotSettings(BaseSettings):
    BOT_REPO_IMAGE_URL: Optional[str] = Field(..., description="URL where the image for the bot is stored")
    BOT_IMAGE_TAG: Optional[str] = Field(..., description="image tag for the bot")
    BOT_APP_SERVICE_PLAN_NAME: Optional[str] = Field(..., description="name of the app service plan to use for the bot")
    BOT_COSMOS_ACCOUNT_NAME: Optional[str] = Field(
        ..., description="name of the cosmos account if not default (<APP_NAME>-cos-<LOCATION>-api)"
    )
    BOT_COSMOS_RESOURCE_GROUP_NAME: Optional[str] = Field(
        ..., description="resource group name where the cosmos is located if not in the same resource group as the bot"
    )
    BOT_ANONYM_NAME: Optional[str] = Field(..., description="-")
    BOT_ANONYM_EMAIL: Optional[str] = Field(..., description="-")
    BOT_ANONYM_ROLES: Optional[str] = Field(..., description="-")
    BOT_ANONYM_OID: Optional[str] = Field(..., description="-")
    BOT_NATS_ENDPOINT: Optional[str] = Field(..., description="NATS endpoint")
    BOT_VERSION: Optional[str] = Field(..., description="version")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )
