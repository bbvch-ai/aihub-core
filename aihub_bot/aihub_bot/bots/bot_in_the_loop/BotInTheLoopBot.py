import logging
import re
from typing import override

from aihub_lib.nats.distributor.events.ExternalAgentEvent import ExternalAgentEvent
from aihub_lib.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from aihub_lib.nats.events.bot_in_the_loop import BotInTheLoop
from aihub_lib.nats.events.bot_in_the_loop.response.BotInTheLoopResponseEvent import BotInTheLoopResponderInfo
from microsoft_agents.hosting.core import ActivityHandler, TurnContext
from nats.aio.client import Client as NATS

from aihub_bot.routes.bot_in_the_loop.BotInTheLoopHandler import BotInTheLoopHandler

logger = logging.getLogger(__name__)


class BotInTheLoopBot(ActivityHandler):
    def __init__(
        self,
        nc: NATS,
        external_agent_event_distributor: ExternalAgentEventDistributor,
        bot_in_the_loop_handler: BotInTheLoopHandler,
    ):
        super().__init__()
        self.nc = nc
        self.external_agent_event_distributor = external_agent_event_distributor
        self.bot_in_the_loop_handler = bot_in_the_loop_handler

    @staticmethod
    def _parse_conversation_id(turn_context: TurnContext, channel: str) -> tuple[str, str] | None:
        conversation_id = turn_context.activity.conversation.id

        if channel == "slack":
            parts = conversation_id.split(":")
            if len(parts) < 4:
                logger.debug(f"Invalid Slack conversation ID format: {conversation_id}")
                return None
            base_conversation_id = ":".join(parts[0:3])
            thread_identifier = parts[3]
            return base_conversation_id, thread_identifier

        elif channel == "msteams":
            parts = conversation_id.split(";")
            if len(parts) != 2:
                logger.debug(f"Invalid Teams conversation ID format: {conversation_id}")
                return None
            base_conversation_id = parts[0]
            teams_message_id_part = parts[1]
            if not teams_message_id_part.startswith("messageid="):
                logger.debug(f"Invalid Teams message ID part format: {teams_message_id_part}")
                return None
            thread_identifier = teams_message_id_part.split("=")[1]
            return base_conversation_id, thread_identifier

        return None

    def _find_matching_thread(self, base_conversation_id: str, thread_identifier: str) -> str | None:
        for thread_id, thread in self.bot_in_the_loop_handler.threads.items():
            if thread.conversation_id == base_conversation_id and thread.thread_identifier == thread_identifier:
                return thread_id
        return None

    @staticmethod
    def _extract_responder_info(turn_context: TurnContext) -> BotInTheLoopResponderInfo | None:
        if not hasattr(turn_context.activity, "from_property") or not turn_context.activity.from_property:
            return None

        responder_info = BotInTheLoopResponderInfo(
            user_id=turn_context.activity.from_property.id,
            user_name=getattr(turn_context.activity.from_property, "name", None),
            additional_info=getattr(turn_context.activity, "channel_data", None),
            aad_object_id=getattr(turn_context.activity.from_property, "aad_object_id", None),
        )

        return responder_info

    @override
    async def on_message_activity(self, turn_context: TurnContext):
        channel_id = turn_context.activity.channel_id
        channel: str

        if channel_id == "slack":
            if not self.is_slack_channel_thread_message(turn_context):
                logger.debug("Not a Slack channel thread message")
                return
            channel = "slack"
        elif channel_id == "msteams":
            channel = "msteams"
        else:
            raise NotImplementedError("Only Slack and Teams channels are supported")

        parsed: tuple[str, str] | None = self._parse_conversation_id(turn_context, channel)
        if parsed is None:
            return

        base_conversation_id, thread_identifier = parsed

        matching_thread_id = self._find_matching_thread(base_conversation_id, thread_identifier)
        if not matching_thread_id:
            logger.debug(
                f"No matching thread found for {channel} channel {base_conversation_id} "
                f"and thread {thread_identifier}"
            )
            return

        bot_in_the_loop_request = self.bot_in_the_loop_handler.threads[matching_thread_id].last_request_event
        responder_info = self._extract_responder_info(turn_context)

        await self.external_agent_event_distributor.distribute_event(
            external_event=ExternalAgentEvent(
                event=BotInTheLoop.response(
                    response=turn_context.activity.text,
                    request_event=bot_in_the_loop_request,
                    responder=responder_info,
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
