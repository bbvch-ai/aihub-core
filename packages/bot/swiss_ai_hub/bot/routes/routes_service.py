import logging

from fastapi import HTTPException, Request, Response
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.hosting.core import ActivityHandler, AgentAuthConfiguration
from microsoft_agents.hosting.core.authorization import AuthTypes
from swiss_ai_hub.core.routes import ChatService

from swiss_ai_hub.bot.persistence.entities.path_entity import Credentials, PathEntity
from swiss_ai_hub.bot.routes.bot_activity_authenticator import BotActivityAuthenticator

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
    async def process_activity(request: Request, agent: ActivityHandler) -> Response:
        """
        Authenticates the inbound activity against the bot configured on the request path, then hands it to the agent.

        The adapter would otherwise run the turn with anonymous claims, so every activity route must go through here.
        """
        path = RoutesService.get_path(request)
        await RoutesService.authenticate_activity(request, path)
        return await RoutesService.get_adapter(path).process(request, agent)

    @staticmethod
    async def authenticate_activity(request: Request, path: str) -> None:
        """Stores the verified claims where the adapter reads them, instead of letting it fall back to anonymous."""
        auth_configuration = RoutesService.get_auth_configuration(path)
        request.scope["claims_identity"] = await BotActivityAuthenticator.authenticate(request, auth_configuration)

    @staticmethod
    def get_auth_configuration(path: str) -> AgentAuthConfiguration:
        credentials = RoutesService.get_credentials(path)
        if credentials is None:
            raise HTTPException(status_code=404, detail=f"No bot configured for path: {path}")
        return AgentAuthConfiguration(**RoutesService._create_auth_configuration_dict(credentials))

    @staticmethod
    def get_adapter(path: str) -> CloudAdapter:
        """
        ### What
        - Returns a cached CloudAdapter for the given path, or creates a new one if not cached.

        ### Why
        - Each path has a unique set of credentials, used for the bot's outbound calls to the channel.
        - Caching prevents repeated MSAL authentication and improves performance.
        """
        if path in RoutesService._adapter_cache:
            logger.debug(f"Using cached CloudAdapter for path: {path}")
            return RoutesService._adapter_cache[path]

        logger.debug(f"Creating new CloudAdapter for path: {path}")
        auth_config = RoutesService.get_auth_configuration(path)
        connection_manager = MsalConnectionManager(connections_configurations={"SERVICE_CONNECTION": auth_config})

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
