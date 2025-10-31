import logging
from typing import Any

from aihub_lib.routes.chat.ChatService import ChatService
from fastapi import Request
from microsoft_agents.authentication.msal import MsalAuth, MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core.authorization import AuthTypes

from aihub_bot.persistence.entities.PathEntity import Credentials, PathEntity

logger = logging.getLogger(__name__)


# Monkey-patch MsalAuth to work around SDK bug with app:// audience validation
# The SDK tries to get a token for app://client_id which Azure doesn't support
_original_get_access_token = MsalAuth.get_access_token


async def _patched_get_access_token(self: MsalAuth, resource: str, scopes: list[str] | None = None) -> str:
    """
    Workaround for Microsoft Agents SDK bug where it requests tokens for app://client_id audience.
    Azure doesn't allow app:// scheme in identifier URIs, only api://.
    For proactive messaging, we reuse the Bot Framework API token instead.
    """
    # If requesting token for app://client_id, use Bot Framework API token instead
    if resource.startswith("app://"):
        logger.warning(
            f"SDK requested token for unsupported audience '{resource}', "
            f"using Bot Framework API token instead"
        )
        # Use Bot Framework scopes instead of the invalid app:// scopes
        bot_framework_scopes = ["https://api.botframework.com/.default"]
        return await _original_get_access_token(self, "https://api.botframework.com", bot_framework_scopes)

    # For all other resources, use original implementation
    return await _original_get_access_token(self, resource, scopes)


# Apply the monkey patch
MsalAuth.get_access_token = _patched_get_access_token  # type: ignore[method-assign]


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
        credentials = RoutesService.get_credentials(path)
        if credentials is None:
            raise ValueError(f"No credentials found for path: {path}")
        auth_config_dict = RoutesService._create_auth_configuration_dict(credentials)

        # Create connection manager with the auth configuration
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
        # Force multi-tenant mode to avoid app:// audience validation issues
        # Single-tenant bots require app://client_id as identifier URI, but Azure doesn't allow app:// scheme
        # Using multi-tenant mode with explicit tenant_id works around this limitation
        config_params: dict[str, str | AuthTypes | list[str]] = {
            "auth_type": AuthTypes.client_secret,
            "client_id": credentials.APP_ID,
            "client_secret": credentials.APP_PASSWORD,
            "scopes": ["https://api.botframework.com/.default"],
        }

        # Always include tenant_id for proper authentication, even in multi-tenant mode
        if credentials.APP_TENANTID:
            config_params["tenant_id"] = credentials.APP_TENANTID

        return config_params

    @staticmethod
    def get_credentials(path: str) -> Credentials | None:
        return PathEntity.get_credentials_by_path(path)
