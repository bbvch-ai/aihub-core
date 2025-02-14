import abc
import logging

from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication

from aihub_bot.persistence.entities.PathEntity import Credentials, PathEntity

logger = logging.getLogger(__name__)


class Service(abc.ABC):
    @staticmethod
    def get_adapter(path: str) -> CloudAdapter:
        credentials: Credentials = PathEntity.get_credentials_by_path(path)
        return CloudAdapter(ConfigurationBotFrameworkAuthentication(credentials))
