import logging
from typing import List

from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount
from llama_index.core.base.llms.types import ChatMessage
from nats.aio.client import Client as NATS

from aihub_bot.persistence.chat.entities.ConversationEntity import Message, User
from aihub_bot.routes.chat.ChatService import ChatService

logger = logging.getLogger(__name__)


class ChatBot(ActivityHandler):
    def __init__(self, nc: NATS, ws_receiver: WebSocketReceiver, agent_class: str, agent_id: str):
        self.nc = nc
        self.ws_receiver = ws_receiver
        self.agent_class = agent_class
        self.agent_id = agent_id

    async def on_conversation_update_activity(self, turn_context: TurnContext):
        ChatService.create_conversation(turn_context.activity.conversation.id, [], [])
        await super().on_conversation_update_activity(turn_context)

    async def on_members_added_activity(self, members_added: List[ChannelAccount], turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                user = User(user_id=member.id)
                ChatService.add_user_to_conversation(turn_context.activity.conversation.id, user)
                return await ChatService.respond_to_user(turn_context, turn_context.activity, "Hello and welcome!")

    async def on_message_activity(self, turn_context: TurnContext):
        user_message = Message(
            user_id=turn_context.activity.from_property.id,
            content=turn_context.activity.text,
            role=turn_context.activity.from_property.role,
        )
        ChatService.add_message_to_conversation(turn_context.activity.conversation.id, user_message)
        persisted_messages: List[Message] = ChatService.get_messages_by_conversation_id(
            turn_context.activity.conversation.id
        )
        messages: List[ChatMessage] = [ChatService.message_to_chat_message(message) for message in persisted_messages]
        response: str = await ChatService.json_chat(
            user_id=turn_context.activity.from_property.id,
            agent_class=self.agent_class,
            agent_id=self.agent_id,
            messages=messages,
            nc=self.nc,
            ws_receiver=self.ws_receiver,
        )
        return await ChatService.respond_to_user(turn_context, turn_context.activity, response)
