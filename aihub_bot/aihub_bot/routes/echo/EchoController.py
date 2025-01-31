from starlette.requests import Request
from starlette.responses import Response

from aihub_bot.routes.Controller import Controller
from aihub_bot.routes.echo.EchoService import EchoService


class EchoController(Controller):

    def __init__(self, route: str = "/echo"):
        super().__init__(route)

    def post_messages(self, route: str = "/") -> "EchoController":
        @self.router.post(route)
        async def post_messages(request: Request) -> Response:
            return await EchoService.process_messages(req=request)

        return self
