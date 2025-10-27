import logging

from aihub_lib.routes.chat.ChatService import ChatService
from fastapi import Request
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import AgentAuthConfiguration
from microsoft_agents.hosting.core.authorization import AuthTypes

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
        auth_config = RoutesService._create_auth_configuration(credentials)

        # Create connection manager with the auth configuration
        connection_manager = MsalConnectionManager(connections_configurations={"SERVICE_CONNECTION": auth_config})

        adapter = CloudAdapter(connection_manager=connection_manager)
        RoutesService._adapter_cache[path] = adapter
        return adapter

    @staticmethod
    def _create_auth_configuration(credentials: Credentials) -> AgentAuthConfiguration:
        """
        ### What
        - Converts legacy credential dict format to AgentAuthConfiguration.

        ### Why
        - The new SDK uses AgentAuthConfiguration instead of simple dicts.
        - This helper method provides backward compatibility with existing PathEntity credentials.
        """
        app_type = credentials.get("APP_TYPE", "MultiTenant")
        auth_type = AuthTypes.MULTI_TENANT if app_type == "MultiTenant" else AuthTypes.SINGLE_TENANT

        config_params = {
            "auth_type": auth_type,
            "client_id": credentials.get("APP_ID"),
            "client_secret": credentials.get("APP_PASSWORD"),
        }

        # Single tenant requires tenant_id
        if auth_type == AuthTypes.SINGLE_TENANT:
            config_params["tenant_id"] = credentials.get("APP_TENANTID")

        return AgentAuthConfiguration(**config_params)

    @staticmethod
    def get_credentials(path: str) -> Credentials:
        return PathEntity.get_credentials_by_path(path)
