from typing import Annotated

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.nats.distributor.dependencies.use_external_event_distributor import use_external_event_distributor
from aihub_lib.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from aihub_lib.routes.Controller import Controller
from botbuilder.integration.aiohttp import CloudAdapter
from fastapi import Body, Depends, Path, Request, Response
from nats.aio.client import Client as NATS

from aihub_bot.bots.chat.agent.AgentChatBot import AgentChatBot
from aihub_bot.bots.chat.agent.StreamAgentChatBot import StreamAgentChatBot
from aihub_bot.routes.activity_model import ActivityModel
from aihub_bot.routes.RoutesService import RoutesService


class AgentChatController(Controller):
    """
    Exposes API endpoints for handling Azure Bot Service interactions with AI agents.

    ### Purpose
    - Acts as an intermediary between the Azure Bot Service and the AI agents.

    ### Key Endpoints
    - **JSON (`/completions/{agent_class}/{agent_id}/json`)**:
      - Returns a complete response only after the full conversation is processed.
      - Ensures structured interactions, useful for logging or non-streaming clients.

    ### Authentication & Access Control
    """

    name = LocaleString(en="Agent Chat")
    description = LocaleString(en="Chat with agents")
    icon = "mage:we-chat"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/agent/chat", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def completions_json(
        self,
        route: str = "/completions/{agent_class}/{agent_id}/json",
        typing_timeout_seconds: int = 60,
    ) -> "AgentChatController":
        """
        Registers an endpoint for JSON-based chat completions.

        ### Functionality
        - Handles Azure Bot Service interactions directed at an AI agent.
        - Waits for the full response.
        - Sends a message Activity with the response to the Azure Bot Service.
        """

        @self.router.post(
            route,
            summary="Synchronous chat completions",
            description="Handles chat completions by sending a single response Activity to the Azure Bot Service.",
            tags=self.tags,
            response_model=None,
            responses={
                200: {
                    "description": "Success",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object", "properties": {}},
                            "example": {},
                        }
                    },
                },
            },
        )
        async def json_chat(
            request: Request,
            _: Annotated[ActivityModel, Body],  # openapi request body
            agent_class: Annotated[str, Path(title="Agent class")],
            agent_id: Annotated[str, Path(title="Agent ID")],
            nc: Annotated[NATS, Depends(use_nats)],
            external_event_distributor: Annotated[
                ExternalAgentEventDistributor, Depends(use_external_event_distributor)
            ],
        ) -> Response:
            path: str = RoutesService.get_path(request)
            chat_bot: AgentChatBot = AgentChatBot(
                nc,
                external_event_distributor,
                agent_class,
                agent_id,
                path,
                typing_timeout_seconds=typing_timeout_seconds,
            )
            adapter: CloudAdapter = RoutesService.get_adapter(path)
            return await adapter.process(request, chat_bot)

        return self

    def completions_stream(
        self,
        route: str = "/completions/{agent_class}/{agent_id}/stream",
        typing_timeout_seconds: int = 60,
    ) -> "AgentChatController":
        """
        Registers an endpoint for streaming chat completions.

        ### Functionality
        - Handles Azure Bot Service interactions directed at an AI agent.
        - Streams responses as they are produced by updating the response Activity.
        """

        @self.router.post(
            route,
            summary="Asynchronous chat completions",
            description="Handles chat completions by updating the response Activity as responses are produced.",
            tags=self.tags,
            response_model=None,
            responses={
                200: {
                    "description": "Success",
                    "content": {
                        "application/json": {
                            "schema": {"type": "object", "properties": {}},
                            "example": {},
                        }
                    },
                },
            },
        )
        async def stream_chat(
            request: Request,
            _: Annotated[ActivityModel, Body],  # openapi request body
            agent_class: Annotated[str, Path(title="Agent class")],
            agent_id: Annotated[str, Path(title="Agent ID")],
            nc: Annotated[NATS, Depends(use_nats)],
            external_event_distributor: Annotated[
                ExternalAgentEventDistributor, Depends(use_external_event_distributor)
            ],
        ) -> Response:
            path: str = RoutesService.get_path(request)
            chat_bot: StreamAgentChatBot = StreamAgentChatBot(
                nc,
                external_event_distributor,
                agent_class,
                agent_id,
                path,
                typing_timeout_seconds=typing_timeout_seconds,
            )
            adapter: CloudAdapter = RoutesService.get_adapter(path)
            return await adapter.process(request, chat_bot)

        return self
