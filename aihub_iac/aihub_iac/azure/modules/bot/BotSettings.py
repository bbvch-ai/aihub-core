from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class BotSettings(BaseSettings):
    BOT_APP_SERVICE_PLAN_NAME: str = Field(..., description="name of the app service plan to use for the bot")
    BOT_REPO_IMAGE_URL: str = Field(..., description="URL where the image for the bot is stored")
    BOT_IMAGE_TAG: str = Field(..., description="image tag for the bot")
    REGISTRY_USER: str = Field(..., description="username used to authenticate with the registry")
    REGISTRY_PAT: str = Field(..., description="personal access token used to authenticate with the registry")
    NATS_ENDPOINT: str = Field(..., description="NATS endpoint")
    CLIENT_ID: str = Field(..., description="client id")  # TODO: really needed? for what?
    TENANT_ID: str = Field(..., description="tenant id")  # TODO: really needed? for what?
    AUTHORITY_URL: str = Field(..., description="authority url")  # TODO: really needed? for what?
    VERSION: str = Field(..., description="version")
    COSMOS_RESOURCE_GROUP_NAME: Optional[str] = Field(
        ..., description="resource group name where the cosmos is located if not in the same resource group as the bot"
    )
    COSMOS_ACCOUNT_NAME: Optional[str] = Field(
        ..., description="name of the cosmos account if not default (<APP_NAME>-cos-<LOCATION>-api)"
    )
    BOT_ANONYM_NAME: str = Field(..., description="-")
    BOT_ANONYM_EMAIL: str = Field(..., description="-")
    BOT_ANONYM_ROLES: str = Field(..., description="-")
    BOT_ANONYM_OID: str = Field(..., description="-")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )
