from typing import Annotated

from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.nats.distributor.dependencies.use_external_event_distributor import use_external_event_distributor
from aihub_lib.nats.distributor.ExternalEventDistributor import ExternalEventDistributor
from aihub_lib.routes.Controller import Controller
from botbuilder.integration.aiohttp import CloudAdapter
from fastapi import Body, Depends, Path, Request, Response
from nats.aio.client import Client as NATS

from aihub_bot.bots.agent.AgentChatBot import AgentChatBot
from aihub_bot.bots.agent.StreamAgentChatBot import StreamAgentChatBot
from aihub_bot.routes.activity_model import ActivityModel
from aihub_bot.routes.agent.AgentChatService import AgentChatService


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

    def __init__(self, route: str = "/agent/chat", is_admin_only=False):
        super().__init__(route, is_admin_only=is_admin_only)

    def completions_json(self, route: str = "/completions/{agent_class}/{agent_id}/json") -> "AgentChatController":
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
            tags=["Chat"],
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
            external_event_distributor: Annotated[ExternalEventDistributor, Depends(use_external_event_distributor)],
        ) -> Response:
            path: str = AgentChatService.get_path(request)
            chat_bot: AgentChatBot = AgentChatBot(nc, external_event_distributor, agent_class, agent_id, path)
            adapter: CloudAdapter = AgentChatService.get_adapter(path)
            return await adapter.process(request, chat_bot)

        return self

    def completions_stream(self, route: str = "/completions/{agent_class}/{agent_id}/stream") -> "AgentChatController":
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
            tags=["Chat"],
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
            external_event_distributor: Annotated[ExternalEventDistributor, Depends(use_external_event_distributor)],
        ) -> Response:
            path: str = AgentChatService.get_path(request)
            chat_bot: StreamAgentChatBot = StreamAgentChatBot(
                nc, external_event_distributor, agent_class, agent_id, path
            )
            adapter: CloudAdapter = AgentChatService.get_adapter(path)
            return await adapter.process(request, chat_bot)

        return self
