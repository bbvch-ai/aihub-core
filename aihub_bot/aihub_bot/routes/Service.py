import abc
import logging

from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from fastapi import Request

from aihub_bot.persistence.entities.PathEntity import Credentials, PathEntity

logger = logging.getLogger(__name__)


class Service(abc.ABC):
    @staticmethod
    def get_adapter(request: Request) -> CloudAdapter:
        path: str = str(request.url).replace(str(request.base_url), "/")
        credentials: Credentials = PathEntity.get_credentials_by_path(path)
        return CloudAdapter(ConfigurationBotFrameworkAuthentication(credentials))
