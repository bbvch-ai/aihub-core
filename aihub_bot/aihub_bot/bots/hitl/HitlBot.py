from typing import override

from botbuilder.core import ActivityHandler, TurnContext
from botframework.connector import Channels
from nats.aio.client import Client as NATS

from aihub_bot.routes.hitl.HitlHandler import HitlHandler
from aihub_lib.nats.distributor.ExternalEventDistributor import ExternalEventDistributor
from aihub_lib.nats.events import HumanInTheLoopResponseEvent
from aihub_lib.nats.publishers.NCPublisher import NCPublisher


class HitlBot(ActivityHandler):
    def __init__(
        self,
        nc: NATS,
        external_event_distributor: ExternalEventDistributor,
        hitl_handler: HitlHandler,
    ):
        super().__init__()
        self.nc = nc
        self.external_event_distributor = external_event_distributor
        self.hitl_handler = hitl_handler

    @override
    async def on_message_activity(self, turn_context: TurnContext):
        # Handle Slack-specific message formatting
        if turn_context.activity.channel_id != Channels.slack:
            raise NotImplementedError("HitlBot only supports Slack channel")

        conversation_id = turn_context.activity.conversation.id

        found = False
        for thread_id, existing_conv_id in self.hitl_handler.thread_to_conversation_mapping.items():
            if conversation_id.startswith(existing_conv_id):
                self.hitl_handler.thread_to_conversation_mapping[thread_id] = conversation_id
                found = True
                break

        if not found:
            raise RuntimeError("Conversation ID not found in thread_to_conversation_mapping")

        hitl_request = self.hitl_handler.conversation_to_hitl_request_mapping.get(conversation_id)

        await self.external_event_distributor.distribute_event(
            external_event=HumanInTheLoopResponseEvent(
                response=turn_context.activity.text,
                request_event=hitl_request,
            ),
            user=turn_context.activity.from_property.id,
        )
