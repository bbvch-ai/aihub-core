from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class BotSettings(BaseSettings):
    BOT_REPO_IMAGE_URL: Optional[str] = Field(default=None, description="URL where the image for the bot is stored")
    BOT_IMAGE_TAG: Optional[str] = Field(default=None, description="image tag for the bot")
    BOT_APP_SERVICE_PLAN_NAME: Optional[str] = Field(
        default=None, description="name of the app service plan to use for the bot"
    )
    BOT_COSMOS_ACCOUNT_NAME: Optional[str] = Field(
        default=None, description="name of the cosmos account if not default (<APP_NAME>-cos-<LOCATION>-api)"
    )
    BOT_COSMOS_RESOURCE_GROUP_NAME: Optional[str] = Field(
        default=None,
        description="resource group name where the cosmos is located if not in the same resource group as the bot",
    )
    BOT_ANONYM_NAME: Optional[str] = Field(default=None, description="-")
    BOT_ANONYM_EMAIL: Optional[str] = Field(default=None, description="-")
    BOT_ANONYM_ROLES: Optional[str] = Field(default=None, description="-")
    BOT_ANONYM_OID: Optional[str] = Field(default=None, description="-")
    BOT_VERSION: Optional[str] = Field(default=None, description="version")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )
