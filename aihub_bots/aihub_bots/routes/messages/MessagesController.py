from starlette.requests import Request
from starlette.responses import Response

from aihub_bots.routes.Controller import Controller
from aihub_bots.routes.messages.MessagesService import MessagesService


class MessagesController(Controller):

    def __init__(self, route: str = "/messages"):
        super().__init__(route)

    def post_messages(self, route: str = "/") -> "MessagesController":
        @self.router.post(route)
        async def post_messages(request: Request) -> Response:
            return await MessagesService.process_messages(request)

        return self
