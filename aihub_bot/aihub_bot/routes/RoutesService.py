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

    # Cache for CloudAdapter instances, keyed by path
    _adapter_cache: dict[str, CloudAdapter] = {}

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
        - Returns a cached CloudAdapter for the given path, or creates a new one if not cached.

        ### Why
        - Each path has a unique set of credentials.
        - The credential is needed to verify that requests are coming from the correct bot service.
        - Caching prevents repeated MSAL authentication and improves performance.
        """
        # Check cache first
        if path in RoutesService._adapter_cache:
            logger.debug(f"Using cached CloudAdapter for path: {path}")
            return RoutesService._adapter_cache[path]

        # Create new adapter and cache it
        logger.debug(f"Creating new CloudAdapter for path: {path}")
        credentials: Credentials = RoutesService.get_credentials(path)
        adapter = CloudAdapter(ConfigurationBotFrameworkAuthentication(credentials))
        RoutesService._adapter_cache[path] = adapter
        return adapter

    @staticmethod
    def get_credentials(path: str) -> Credentials:
        return PathEntity.get_credentials_by_path(path)
