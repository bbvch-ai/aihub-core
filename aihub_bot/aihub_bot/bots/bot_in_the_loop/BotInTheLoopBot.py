import logging

from typing_extensions import override

from aihub_lib.nats.distributor.ExternalEventDistributor import ExternalEventDistributor
from botbuilder.core import ActivityHandler, TurnContext
from botframework.connector import Channels
from nats.aio.client import Client as NATS

from aihub_bot.routes.bot_in_the_loop.BotInTheLoopHandler import BotInTheLoopHandler
from aihub_lib.nats.events.bot_in_the_loop import BotInTheLoopResponseEvent

logger = logging.getLogger(__name__)


class BotInTheLoopBot(ActivityHandler):
    def __init__(
        self,
        nc: NATS,
        external_event_distributor: ExternalEventDistributor,
        bot_in_the_loop_handler: BotInTheLoopHandler,
    ):
        super().__init__()
        self.nc = nc
        self.external_event_distributor = external_event_distributor
        self.bot_in_the_loop_handler = bot_in_the_loop_handler

    @override
    async def on_message_activity(self, turn_context: TurnContext):
        # Handle Slack-specific message formatting
        if turn_context.activity.channel_id != Channels.slack:
            raise NotImplementedError("BotInTheLoopBot only supports Slack channel")

        conversation_id = turn_context.activity.conversation.id

        found = False
        for thread_id, existing_conv_id in self.bot_in_the_loop_handler.thread_to_conversation_mapping.items():
            if conversation_id.startswith(existing_conv_id):
                self.bot_in_the_loop_handler.thread_to_conversation_mapping[thread_id] = conversation_id
                found = True
                break

        if not found:
            self.bot_in_the_loop_handler.slack_conversation = TurnContext.get_conversation_reference(
                turn_context.activity
            )
            logger.info("New Slack conversation ID set: %s", conversation_id)
            return await turn_context.send_activity(f"New Slack channel ID set: {conversation_id}")

        bot_in_the_loop_request = self.bot_in_the_loop_handler.conversation_to_bot_in_the_loop_request_mapping.get(
            conversation_id
        )

        await self.external_event_distributor.distribute_event(
            external_event=BotInTheLoopResponseEvent(
                response=turn_context.activity.text,
                request_event=bot_in_the_loop_request,
            ),
            user=turn_context.activity.from_property.id,
        )
