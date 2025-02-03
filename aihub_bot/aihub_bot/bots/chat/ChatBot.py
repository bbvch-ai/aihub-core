import logging
from typing import Dict, List

from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount, Activity
from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage
from nats.aio.client import Client as NATS

from aihub_lib.routes.chat.ChatService import ChatService, JsonResources
from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver

logger = logging.getLogger(__name__)


class ChatBot(ActivityHandler):
    messages: Dict[str, List[ChatMessage]] = {}
    users: Dict[str, str] = {}

    def __init__(self, nc: NATS, ws_receiver: WebSocketReceiver, agent_class: str, agent_id: str):
        self.nc = nc
        self.ws_receiver = ws_receiver
        self.agent_class = agent_class
        self.agent_id = agent_id

    @staticmethod
    def _save_user(from_property_id: str):
        ChatBot.users[from_property_id] = str(ObjectId())

    @staticmethod
    def _get_user_id(from_property_id: str) -> str:
        if from_property_id not in ChatBot.users:
            ChatBot._save_user(from_property_id)
        return ChatBot.users[from_property_id]

    @staticmethod
    def _save_chat_message(conversation_id: str, text: str):
        if conversation_id not in ChatBot.messages:
            ChatBot.messages[conversation_id] = []
        ChatBot.messages[conversation_id].append(ChatMessage(content=text))

    @staticmethod
    def _get_chat_messages(conversation_id: str) -> List[ChatMessage]:
        if conversation_id in ChatBot.messages:
            return ChatBot.messages[conversation_id]
        return []

    async def _json_chat(
        self,
        user_id: str,
        messages: List[ChatMessage],
        nc: NATS,
        ws_receiver: WebSocketReceiver,
    ) -> str:
        resources: JsonResources = await ChatService.start_json_chat_interaction(
            user_oid=user_id,
            agent_class=self.agent_class,
            agent_id=self.agent_id,
            messages=messages,
            nc=nc,
            ws_receiver=ws_receiver,
        )

        # Wait until all events are processed
        await resources.stop_event.wait()
        await resources.subscriber.stop()

        # Construct final JSON response
        return ChatService.build_json_response_content(resources.chunk_events)

    async def on_members_added_activity(self, members_added: [ChannelAccount], turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                self._save_user(turn_context.activity.from_property.id)
                await turn_context.send_activity("Hello and welcome!")

    async def on_message_activity(self, turn_context: TurnContext):
        activity: Activity = turn_context.activity
        self._save_chat_message(activity.conversation.id, activity.text)
        messages: List[ChatMessage] = self._get_chat_messages(activity.conversation.id)
        user_id: str = self._get_user_id(activity.from_property.id)
        response: str = await self._json_chat(user_id, messages, self.nc, self.ws_receiver)
        return await turn_context.send_activity(response)
