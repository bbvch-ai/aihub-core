from typing import Callable, Dict, cast

from aihub_lib.nats.events import DisplayEvent, HumanInTheLoopRequestEvent
from aihub_lib.nats.topics import AgentTopic
from botbuilder.core import TurnContext
from botbuilder.integration.aiohttp import CloudAdapter
from botbuilder.schema import ConversationAccount, ConversationReference
from botframework.connector import Channels
from httpx import Request


class BotInTheLoopHandler:
    def __init__(self):
        self.thread_to_conversation_mapping: Dict[str, str] = {}
        self.conversation_to_bot_in_the_loop_request_mapping: Dict[str, HumanInTheLoopRequestEvent] = {}

    async def handle_display_event(self, event: DisplayEvent, _: AgentTopic):
        if event.is_bot_in_the_loop_request_event:
            self._handle_bot_in_the_loop_request(cast(event, HumanInTheLoopRequestEvent))
        else:
            return

    def _handle_bot_in_the_loop_request(self, event: HumanInTheLoopRequestEvent):
        adapter = CloudAdapter()
        thread_id = event.topic.thread_id
        if thread_id in self.thread_to_conversation_mapping:
            slack_channel_id = self.thread_to_conversation_mapping[thread_id]
        else:
            slack_channel_id = "B1234567890:T1234567890:C1234567890"
            self.thread_to_conversation_mapping[thread_id] = slack_channel_id

        self.conversation_to_bot_in_the_loop_request_mapping[slack_channel_id] = event

        conversation = ConversationReference(
            channel_id=Channels.slack,
            conversation=ConversationAccount(
                id=f"{slack_channel_id}",
            ),
        )
        adapter.continue_conversation(
            reference=conversation,
            callback=self._bot_in_the_loop_callback(event),
        )

    def _bot_in_the_loop_callback(self, event: HumanInTheLoopRequestEvent) -> Callable[[TurnContext], None]:
        return lambda turn_context: turn_context.send_activity(event.question)

    @staticmethod
    def use_bot_in_the_loop_handler(request: Request) -> "BotInTheLoopHandler":
        return request.app.state.bot_in_the_loop_handler
