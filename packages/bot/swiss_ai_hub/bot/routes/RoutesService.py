import logging

from fastapi import Request
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core.authorization import AuthTypes
from swiss_ai_hub.core.routes.chat.ChatService import ChatService

from swiss_ai_hub.bot.persistence.entities.PathEntity import Credentials, PathEntity

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
        if path in RoutesService._adapter_cache:
            logger.debug(f"Using cached CloudAdapter for path: {path}")
            return RoutesService._adapter_cache[path]

        logger.debug(f"Creating new CloudAdapter for path: {path}")
        credentials = RoutesService.get_credentials(path)
        if credentials is None:
            raise ValueError(f"No credentials found for path: {path}")
        auth_config_dict = RoutesService._create_auth_configuration_dict(credentials)

        # MsalConnectionManager expects a dict that it will use to create AgentAuthConfiguration
        connection_manager = MsalConnectionManager(connections_configurations={"SERVICE_CONNECTION": auth_config_dict})

        adapter = CloudAdapter(connection_manager=connection_manager)
        RoutesService._adapter_cache[path] = adapter
        return adapter

    @staticmethod
    def _create_auth_configuration_dict(credentials: Credentials) -> dict[str, str | AuthTypes | list[str]]:
        """
        ### What
        - Converts Credentials object to a dictionary for AgentAuthConfiguration.

        ### Why
        - MsalConnectionManager expects a dict that it will use to create AgentAuthConfiguration.
        - This helper method converts PathEntity credentials to the required dict format.
        """
        config_params: dict[str, str | AuthTypes | list[str]] = {
            "auth_type": AuthTypes.client_secret,
            "client_id": credentials.APP_ID,
            "client_secret": credentials.APP_PASSWORD,
            "scopes": ["https://api.botframework.com/.default"],
        }

        # Include tenant_id for proper authentication
        if credentials.APP_TENANTID:
            config_params["tenant_id"] = credentials.APP_TENANTID

        return config_params

    @staticmethod
    def get_credentials(path: str) -> Credentials | None:
        return PathEntity.get_credentials_by_path(path)
