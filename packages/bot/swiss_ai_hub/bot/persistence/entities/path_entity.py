from typing import Self

from beanie import Document
from pydantic import BaseModel
from pymongo import ASCENDING, IndexModel


class Credentials(BaseModel):
    APP_TYPE: str | None = None
    APP_ID: str | None = None
    APP_PASSWORD: str | None = None
    APP_TENANTID: str | None = None


class PathEntity(Document):
    """
    Represents the configuration for a given path/endpoint and therefore for a specific bot.

    ### Purpose
    - Stores the credentials required to authenticate with a given bot.
    - Stores the system message with instructions for the bot.

    ### Usage
    This class enables the AI Hub to configure deployed bots with the necessary credentials and system messages
    directly in the database.
    """

    path: str
    credentials: Credentials
    system_message: str | None = None
    slack_token: str | None = None

    class Settings:
        name = "bot_paths"
        keep_nulls = False
        indexes = [IndexModel([("path", ASCENDING)], unique=True)]

    @classmethod
    async def get_by_path(cls, path: str) -> Self | None:
        return await cls.find_one({"path": path})

    @classmethod
    async def get_credentials_by_path(cls, path: str) -> Credentials | None:
        doc = await cls.get_by_path(path)
        return doc.credentials if doc else None

    @classmethod
    async def get_system_message_by_path(cls, path: str) -> str | None:
        doc = await cls.get_by_path(path)
        return doc.system_message if doc else None

    @classmethod
    async def get_slack_token_by_path(cls, path: str) -> str | None:
        doc = await cls.get_by_path(path)
        return doc.slack_token if doc else None
