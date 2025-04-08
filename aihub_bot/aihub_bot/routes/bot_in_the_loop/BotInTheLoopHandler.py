from typing import Callable, Dict, cast

from aihub_lib.nats.events import BaseEvent
from aihub_lib.nats.events.bot_in_the_loop import BotInTheLoopRequestEvent
from aihub_lib.nats.topics import AgentTopic
from botbuilder.core import TurnContext
from botbuilder.integration.aiohttp import CloudAdapter
from botbuilder.schema import ConversationAccount, ConversationReference
from botframework.connector import Channels
from fastapi import Request


class BotInTheLoopHandler:
    def __init__(self):
        self.thread_to_conversation_mapping: Dict[str, str] = {}
        self.conversation_to_bot_in_the_loop_request_mapping: Dict[str, BotInTheLoopRequestEvent] = {}

    async def handle_event(self, event: BaseEvent, topic: AgentTopic):
        if event.is_bitl_request_event:
            await self._handle_bot_in_the_loop_request(event, topic)
        else:
            return

    async def _handle_bot_in_the_loop_request(
        self,
        event: BotInTheLoopRequestEvent,
        topic: AgentTopic,
    ):
        adapter = CloudAdapter()
        thread_id = topic.thread_id
        if thread_id in self.thread_to_conversation_mapping:
            slack_channel_id = self.thread_to_conversation_mapping[thread_id]
        else:
            slack_channel_id = "B08D8FP20TZ:T08AZPNJV33:C08MK7Z8GU9"
            self.thread_to_conversation_mapping[thread_id] = slack_channel_id

        self.conversation_to_bot_in_the_loop_request_mapping[slack_channel_id] = event

        conversation = ConversationReference(
            channel_id=Channels.slack,
            conversation=ConversationAccount(
                id=f"{slack_channel_id}",
            ),
        )
        question: str = event.question
        await adapter.continue_conversation(
            reference=conversation,
            callback=self._bot_in_the_loop_callback(question),
        )

    def _bot_in_the_loop_callback(self, question: str) -> Callable[[TurnContext], None]:
        return lambda turn_context: turn_context.send_activity(question)

    @staticmethod
    def use_bot_in_the_loop_handler(request: Request) -> "BotInTheLoopHandler":
        return request.app.state.bot_in_the_loop_handler
