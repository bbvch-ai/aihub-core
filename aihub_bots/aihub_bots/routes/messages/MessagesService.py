import logging
from datetime import datetime

from aiohttp.web import Request, Response
from botbuilder.core import TurnContext
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from botbuilder.schema import Activity, ActivityTypes
from nats.aio.client import Client as NATS

from aihub_bots.bots.ChatBot import ChatBot
from aihub_bots.routes.messages.DefaultConfig import DefaultConfig
from aihub_bots.sockets.receiver.WebSocketReceiver import WebSocketReceiver


class MessagesService:

    CONFIG = DefaultConfig()
    ADAPTER = CloudAdapter(ConfigurationBotFrameworkAuthentication(CONFIG))

    @staticmethod
    # Catch-all for errors.
    async def on_error(context: TurnContext, error: Exception):
        logging.error(f"\n [on_turn_error] unhandled error: {error}")

        # Send a message to the user
        await context.send_activity("The bot encountered an error or bug.")

        # Send a trace activity if we're talking to the Bot Framework Emulator
        if context.activity.channel_id == "emulator":
            # Create a trace activity that contains the error object
            trace_activity = Activity(
                label="TurnError",
                name="on_turn_error Trace",
                timestamp=datetime.now(),
                type=ActivityTypes.trace,
                value=f"{error}",
                value_type="https://www.botframework.com/schemas/error",
            )
            # Send a trace activity, which will be displayed in Bot Framework Emulator
            await context.send_activity(trace_activity)

    ADAPTER.on_turn_error = on_error

    @staticmethod
    async def process_messages(nc: NATS, req: Request, ws_receiver: WebSocketReceiver) -> Response:
        return await MessagesService.ADAPTER.process(req, ChatBot(nc, ws_receiver))
