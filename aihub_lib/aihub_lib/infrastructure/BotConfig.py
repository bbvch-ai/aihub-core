from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotConfig(BaseSettings):
    BOT_DB_NAME: str = Field(
        "aihub_bot",
        pattern=r"^[A-Za-z]+$",
        description="Database holding conversations and configurations for the bot",
    )
