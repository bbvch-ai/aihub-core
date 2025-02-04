from typing import Annotated

from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.routes.Controller import Controller
from aihub_lib.sockets.receiver.dependencies.use_ws_receiver import use_ws_receiver
from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver
from fastapi import Depends, Path
from nats.aio.client import Client as NATS
from starlette.requests import Request
from starlette.responses import Response

from aihub_bot.bots.chat.ChatBot import ChatBot
from aihub_bot.routes.chat.ChatService import ChatService


class ChatController(Controller):
    def __init__(self, route: str = "/chat"):
        super().__init__(route)

    def completions_json(self, route: str = "/completions/{agent_class}/{agent_id}/json") -> "ChatController":
        @self.router.post(route)
        async def json_chat(
            request: Request,
            agent_class: Annotated[str, Path(title="Agent class")],
            agent_id: Annotated[str, Path(title="Agent ID")],
            nc: Annotated[NATS, Depends(use_nats)],
            ws_receiver: Annotated[WebSocketReceiver, Depends(use_ws_receiver)],
        ) -> Response:
            chat_bot: ChatBot = ChatBot(nc, ws_receiver, agent_class, agent_id)
            return await ChatService.ADAPTER.process(request, chat_bot)

        return self
