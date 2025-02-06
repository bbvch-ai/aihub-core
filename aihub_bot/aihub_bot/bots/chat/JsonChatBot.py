import logging
from typing import List

from botbuilder.core import TurnContext
from llama_index.core.base.llms.types import ChatMessage
from typing_extensions import override

from aihub_bot.bots.chat.ChatBot import ChatBot
from aihub_bot.persistence.chat.entities.ConversationEntity import Message
from aihub_bot.routes.chat.ChatService import ChatService

logger = logging.getLogger(__name__)


class JsonChatBot(ChatBot):
    @override
    async def on_message_activity(self, turn_context: TurnContext):
        """
        A message activity is sent when a user sends a message to the bot.

        Persists user messages in the database and sends them to the AI agent for processing.
        Sends the message history to the agent for context.
        The agent's response is also persisted in the database and sent back to the user.
        """
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
