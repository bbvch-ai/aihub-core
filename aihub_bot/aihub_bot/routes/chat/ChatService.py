from aiohttp.web import Request, Response
from nats.aio.client import Client as NATS

from aihub_bot.bots.chat.ChatBot import ChatBot
from aihub_bot.routes.Service import Service
from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver


class ChatService(Service):

    @staticmethod
    async def process_messages(
        nc: NATS,
        req: Request,
        ws_receiver: WebSocketReceiver,
        agent_class: str,
        agent_id: str,
    ) -> Response:
        chat_bot: ChatBot = ChatBot(nc, ws_receiver, agent_class, agent_id)
        return await ChatService.ADAPTER.process(req, chat_bot)
