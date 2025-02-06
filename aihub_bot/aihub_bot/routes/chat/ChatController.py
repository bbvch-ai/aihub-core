from typing import Annotated

from fastapi import Depends, Path, Body
from nats.aio.client import Client as NATS
from starlette.requests import Request
from starlette.responses import JSONResponse

from aihub_bot.bots.chat.JsonChatBot import JsonChatBot
from aihub_bot.bots.chat.StreamChatBot import StreamChatBot
from aihub_bot.routes.activity_model import ActivityModel
from aihub_bot.routes.chat.ChatService import ChatService
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.routes.Controller import Controller
from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver
from aihub_lib.sockets.receiver.dependencies.use_ws_receiver import use_ws_receiver


class ChatController(Controller):
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

    def __init__(self, route: str = "/chat"):
        super().__init__(route)

    def completions_json(self, route: str = "/completions/{agent_class}/{agent_id}/json") -> "ChatController":
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
                    "content": {"application/json": {
                        "schema": {"type": "object", "properties": {}},
                        "example": {},
                    }},
                },
            },
        )
        async def json_chat(
            request: Request,
            _: Annotated[ActivityModel, Body],  # openapi request body
            agent_class: Annotated[str, Path(title="Agent class")],
            agent_id: Annotated[str, Path(title="Agent ID")],
            nc: Annotated[NATS, Depends(use_nats)],
            ws_receiver: Annotated[WebSocketReceiver, Depends(use_ws_receiver)],
        ) -> JSONResponse:
            chat_bot: JsonChatBot = JsonChatBot(nc, ws_receiver, agent_class, agent_id)
            return await ChatService.ADAPTER.process(request, chat_bot)

        return self

    def completions_stream(self, route: str = "/completions/{agent_class}/{agent_id}/stream") -> "ChatController":
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
                    "content": {"application/json": {
                        "schema": {"type": "object", "properties": {}},
                        "example": {},
                    }},
                },
            },
        )
        async def stream_chat(
            request: Request,
            _: Annotated[ActivityModel, Body],  # openapi request body
            agent_class: Annotated[str, Path(title="Agent class")],
            agent_id: Annotated[str, Path(title="Agent ID")],
            nc: Annotated[NATS, Depends(use_nats)],
            ws_receiver: Annotated[WebSocketReceiver, Depends(use_ws_receiver)],
        ) -> JSONResponse:
            chat_bot: StreamChatBot = StreamChatBot(nc, ws_receiver, agent_class, agent_id)
            return await ChatService.ADAPTER.process(request, chat_bot)

        return self
