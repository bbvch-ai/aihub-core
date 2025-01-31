from typing import Annotated

from fastapi import Depends
from nats.aio.client import Client as NATS
from starlette.requests import Request
from starlette.responses import Response

from aihub_bots.nats.dependencies.use_nats import use_nats
from aihub_bots.routes.Controller import Controller
from aihub_bots.routes.messages.MessagesService import MessagesService
from aihub_bots.sockets.receiver.dependencies.use_ws_receiver import use_ws_receiver


class MessagesController(Controller):

    def __init__(self, route: str = "/messages"):
        super().__init__(route)

    def post_messages(self, route: str = "/") -> "MessagesController":
        @self.router.post(route)
        async def post_messages(
            request: Request,
            nc: Annotated[NATS, Depends(use_nats)],
            ws_receiver: Annotated[None, Depends(use_ws_receiver)],
        ) -> Response:
            return await MessagesService.process_messages(req=request, nc=nc, ws_receiver=ws_receiver)

        return self
