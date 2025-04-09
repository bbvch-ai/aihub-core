import logging
import re

from aihub_lib.nats.distributor.events.ExternalEvent import ExternalEvent
from aihub_lib.nats.distributor.ExternalEventDistributor import ExternalEventDistributor
from aihub_lib.nats.events.bot_in_the_loop import BotInTheLoop
from botbuilder.core import ActivityHandler, TurnContext
from botframework.connector import Channels
from nats.aio.client import Client as NATS
from typing_extensions import override

from aihub_bot.routes.bot_in_the_loop.BotInTheLoopHandler import BotInTheLoopHandler

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

        if not self.is_slack_channel_thread_message(turn_context):
            logger.debug("Not a Slack channel thread message")
            return

        conversation_id = turn_context.activity.conversation.id

        # Parse the conversation ID to extract the full channel ID and thread ID
        # Format is: {bot_id}:{team_id}:{channel_id}:{thread_ts}
        parts = conversation_id.split(":")
        if len(parts) < 4:
            logger.debug(f"Invalid Slack conversation ID format: {conversation_id}")
            return

        # The full channel ID is the combination of bot_id:team_id:channel_id
        full_channel_id = ":".join(parts[0:3])
        slack_thread_ts = parts[3]

        # Find the corresponding thread in the handler's threads dictionary
        matching_thread_id = None
        for thread_id, thread in self.bot_in_the_loop_handler.threads.items():
            if thread.slack_channel_id == full_channel_id and thread.slack_thread_id == slack_thread_ts:
                matching_thread_id = thread_id
                break

        if not matching_thread_id:
            logger.debug(f"No matching thread found for Slack channel {full_channel_id} and thread {slack_thread_ts}")
            return

        # Get the original request event
        bot_in_the_loop_request = self.bot_in_the_loop_handler.threads[matching_thread_id].last_request_event

        # Distribute the response event
        await self.external_event_distributor.distribute_event(
            external_event=ExternalEvent(
                event=BotInTheLoop.response(
                    response=turn_context.activity.text,
                    request_event=bot_in_the_loop_request,
                ),
                thread_id=bot_in_the_loop_request.topic.thread_id,
                display_id=bot_in_the_loop_request.topic.display_id,
            ),
            user=bot_in_the_loop_request.user,
        )

    @staticmethod
    def is_slack_channel_thread_message(turn_context: TurnContext) -> bool:
        conversation_id: str = turn_context.activity.conversation.id
        channel_id_regex = re.compile(r"^B[0-9A-Z]+:T[0-9A-Z]+:C[0-9A-Z]+:\d+[.]\d+$")
        return channel_id_regex.match(conversation_id) is not None
