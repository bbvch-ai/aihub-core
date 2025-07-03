from typing import Annotated, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    BOT_REPO_IMAGE_URL: Annotated[Optional[str], Field(description="URL where the image for the bot is stored")] = None
    BOT_IMAGE_TAG: Annotated[Optional[str], Field(description="image tag for the bot")] = None
    BOT_APP_SERVICE_PLAN_NAME: Annotated[
        Optional[str], Field(description="name of the app service plan to use for the bot")
    ] = None
    BOT_COSMOS_ACCOUNT_NAME: Annotated[
        Optional[str], Field(description="name of the cosmos account if not default (<APP_NAME>-cos-<LOCATION>-api)")
    ] = None
    BOT_COSMOS_RESOURCE_GROUP_NAME: Annotated[
        Optional[str],
        Field(
            description="resource group name where the cosmos is located if not in the same resource group as the bot",
        ),
    ] = None
    BOT_ANONYM_NAME: Annotated[Optional[str], Field(description="-")] = None
    BOT_ANONYM_EMAIL: Annotated[Optional[str], Field(description="-")] = None
    BOT_ANONYM_ROLES: Annotated[Optional[str], Field(description="-")] = None
    BOT_ANONYM_OID: Annotated[Optional[str], Field(description="-")] = None
    BOT_VERSION: Annotated[Optional[str], Field(description="version")] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        env_file_encoding="utf-8",
        extra="ignore",
    )
