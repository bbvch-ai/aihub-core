import logging

from microsoft_agents.hosting.core import AgentAuthConfiguration

from aihub_lib.routes.chat.ChatService import ChatService
from microsoft_agents.hosting.aiohttp import CloudAdapter
from microsoft_agents.authentication.msal import MsalConnectionManager
from microsoft_agents.activity import load_configuration_from_env

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
        credentials: Credentials = RoutesService.get_credentials(path)
        auth: AgentAuthConfiguration = credentials.to_agent_auth_configuration()
        connections_configurations: dict = {
            "CONNECTIONS": {
                "SERVICE_CONNECTION": {
                    "SETTINGS": {
                        "CLIENTID": auth.CLIENT_ID,
                        "CLIENTSECRET": auth.CLIENT_SECRET,
                        "TENANTID": auth.TENANT_ID,
                    }
                }
            }
        }
        return CloudAdapter(
            connection_manager=MsalConnectionManager(**connections_configurations),
        )

    @staticmethod
    def get_credentials(path: str) -> Credentials:
        return PathEntity.get_credentials_by_path(path)
