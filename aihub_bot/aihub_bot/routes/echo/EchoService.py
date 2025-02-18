from aiohttp.web import Request, Response

from aihub_bot.bots.echo.EchoBot import EchoBot
from aihub_bot.routes.Service import Service


class EchoService(Service):
    BOT = EchoBot()

    @staticmethod
    async def process_messages(req: Request) -> Response:
        return await EchoService.get_adapter(req).process(req, EchoService.BOT)
