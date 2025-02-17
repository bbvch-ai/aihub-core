import abc
import logging
from typing import Optional

from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from fastapi import Request

from aihub_bot.persistence.entities.PathEntity import Credentials, PathEntity

logger = logging.getLogger(__name__)


class Service(abc.ABC):
    @staticmethod
    def get_path(request: Request) -> str:
        return str(request.url).replace(str(request.base_url), "/")

    @staticmethod
    def get_adapter(path: str) -> CloudAdapter:
        credentials: Credentials = PathEntity.get_credentials_by_path(path)
        return CloudAdapter(ConfigurationBotFrameworkAuthentication(credentials))

    @staticmethod
    def get_system_message(path: str, username: str) -> Optional[str]:
        system_message: Optional[str] = PathEntity.get_system_message_by_path(path)
        if system_message is None:
            return None
        return system_message.format(username=username)
