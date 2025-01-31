from typing import Annotated

from fastapi import Depends
from nats.aio.client import Client as NATS
from starlette.requests import Request
from starlette.responses import Response

from aihub_bot.routes.Controller import Controller
from aihub_bot.routes.chat.ChatService import ChatService
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver
from aihub_lib.sockets.receiver.dependencies.use_ws_receiver import use_ws_receiver


class ChatController(Controller):

    def __init__(self, route: str = "/chat"):
        super().__init__(route)

    def post_messages(self, route: str = "/") -> "ChatController":
        @self.router.post(route)
        async def post_messages(
            request: Request,
            nc: Annotated[NATS, Depends(use_nats)],
            ws_receiver: Annotated[WebSocketReceiver, Depends(use_ws_receiver)],
        ) -> Response:
            return await ChatService.process_messages(req=request, nc=nc, ws_receiver=ws_receiver)

        return self
