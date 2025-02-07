import abc
import logging
from datetime import datetime

from botbuilder.core import TurnContext
from botbuilder.integration.aiohttp import CloudAdapter, ConfigurationBotFrameworkAuthentication
from botbuilder.schema import Activity, ActivityTypes

from aihub_bot.bots.DefaultConfig import DefaultConfig

logger = logging.getLogger(__name__)


class Service(abc.ABC):
    CONFIG = DefaultConfig()
    ADAPTER = CloudAdapter(ConfigurationBotFrameworkAuthentication(CONFIG))

    @staticmethod
    async def on_error(context: TurnContext, error: Exception):
        logger.error(f"\n [on_turn_error] unhandled error: {error}")

        await context.send_activity("The bot encountered an error or bug.")

        # Send a trace activity if we're talking to the Bot Framework Emulator
        if context.activity.channel_id == "emulator":
            trace_activity = Activity(
                label="TurnError",
                name="on_turn_error Trace",
                timestamp=datetime.now(),
                type=ActivityTypes.trace,
                value=f"{error}",
                value_type="https://www.botframework.com/schemas/error",
            )
            await context.send_activity(trace_activity)

    ADAPTER.on_turn_error = on_error
