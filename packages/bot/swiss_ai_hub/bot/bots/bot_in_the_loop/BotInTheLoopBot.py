import logging
import re
from typing import override

from microsoft_agents.activity import Channels
from microsoft_agents.hosting.core import ActivityHandler, TurnContext
from nats.aio.client import Client as NATS
from swiss_ai_hub.core.nats.distributor.events.ExternalAgentEvent import ExternalAgentEvent
from swiss_ai_hub.core.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from swiss_ai_hub.core.nats.events.bot_in_the_loop import BotInTheLoop
from swiss_ai_hub.core.nats.events.bot_in_the_loop.response.BotInTheLoopResponseEvent import BotInTheLoopResponderInfo

from swiss_ai_hub.bot.routes.bot_in_the_loop.BotInTheLoopHandler import BotInTheLoopHandler

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
    def _parse_conversation_id(turn_context: TurnContext, channel: Channels) -> tuple[str, str] | None:
        conversation_id = turn_context.activity.conversation.id

        if channel == Channels.slack:
            parts = conversation_id.split(":")
            if len(parts) < 4:
                logger.debug(f"Invalid Slack conversation ID format: {conversation_id}")
                return None
            base_conversation_id = ":".join(parts[0:3])
            thread_identifier = parts[3]
            return base_conversation_id, thread_identifier

        elif channel == Channels.ms_teams:
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
        conversation_id = turn_context.activity.conversation.id
        message_text = turn_context.activity.text

        logger.info(
            f"[BITL] Received message activity: channel={channel_id}, "
            f"conversation_id={conversation_id}, text={message_text!r}"
        )

        channel: Channels

        if channel_id == Channels.slack:
            is_thread_msg = self.is_slack_channel_thread_message(turn_context)
            logger.info(f"[BITL] Slack message - is_thread_message={is_thread_msg}")
            if not is_thread_msg:
                logger.info(f"[BITL] Ignoring non-thread Slack message: {conversation_id}")
                return
            channel = Channels.slack
        elif channel_id == Channels.ms_teams:
            channel = Channels.ms_teams
        else:
            logger.warning(f"[BITL] Unsupported channel: {channel_id}")
            raise NotImplementedError("Only Slack and Teams channels are supported")

        parsed: tuple[str, str] | None = self._parse_conversation_id(turn_context, channel)
        if parsed is None:
            logger.warning(f"[BITL] Failed to parse conversation ID: {conversation_id}")
            return

        base_conversation_id, thread_identifier = parsed
        logger.info(f"[BITL] Parsed conversation: base={base_conversation_id}, thread={thread_identifier}")

        # Log all tracked threads for debugging
        logger.info(f"[BITL] Currently tracked threads ({len(self.bot_in_the_loop_handler.threads)}):")
        for tid, thread in self.bot_in_the_loop_handler.threads.items():
            logger.info(
                f"[BITL]   - thread_id={tid}, conv_id={thread.conversation_id}, "
                f"thread_identifier={thread.thread_identifier}"
            )

        matching_thread_id = self._find_matching_thread(base_conversation_id, thread_identifier)
        if not matching_thread_id:
            logger.warning(
                f"[BITL] No matching thread found for {channel.value} channel "
                f"base_conversation_id={base_conversation_id}, thread_identifier={thread_identifier}"
            )
            return

        logger.info(f"[BITL] Found matching thread: {matching_thread_id}")

        bot_in_the_loop_request = self.bot_in_the_loop_handler.threads[matching_thread_id].last_request_event
        responder_info = self._extract_responder_info(turn_context)

        logger.info(
            f"[BITL] Distributing response event: thread_id={bot_in_the_loop_request.topic.thread_id}, "
            f"display_id={bot_in_the_loop_request.topic.display_id}, response={message_text!r}"
        )

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

        logger.info("[BITL] Response event distributed successfully")

    @staticmethod
    def is_slack_channel_thread_message(turn_context: TurnContext) -> bool:
        conversation_id: str = turn_context.activity.conversation.id
        channel_id_regex = re.compile(r"^B[0-9A-Z]+:T[0-9A-Z]+:C[0-9A-Z]+:\d+[.]\d+$")
        return channel_id_regex.match(conversation_id) is not None
