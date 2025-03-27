import logging

from aihub_lib.routes.chat.ChatService import ChatService
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from fastapi import Request

from aihub_bot.persistence.entities.PathEntity import Credentials, PathEntity


logger = logging.getLogger(__name__)


class RoutesService(ChatService):
    """
    ### What
    - Shared functionality for all ChatControllers and ChatBots.
    """

    @staticmethod
    def get_path(request: Request) -> str:
        """
        ### What
        - Returns the path/endpoint of the request.

        ### Why
        - Each endpoint can be configured in the database.
        - The path is the key to access this configuration.
        - See `PathEntity`.
        """
        return str(request.url).replace(str(request.base_url), "/")

    @staticmethod
    def get_adapter(path: str) -> CloudAdapter:
        """
        ### What
        - Returns the adapter for the given path.

        ### Why
        - Each path has a unique set of credentials.
        - The credential is needed to verify that requests are coming from the correct bot service.
        """
        credentials: Credentials = PathEntity.get_credentials_by_path(path)
        return CloudAdapter(ConfigurationBotFrameworkAuthentication(credentials))
