from typing import List

from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver
from botbuilder.core import TurnContext
from llama_index.core.base.llms.types import ChatMessage
from nats.aio.client import Client as NATS
from typing_extensions import override

from aihub_bot.bots.chat.ChatBot import ChatBot
from aihub_bot.persistence.chat.entities.ConversationEntity import Message
from aihub_bot.routes.chat.agent.AgentChatService import AgentChatService


class JsonAgentChatBot(ChatBot):
    def __init__(self, nc: NATS, ws_receiver: WebSocketReceiver, agent_class: str, agent_id: str):
        self.nc = nc
        self.ws_receiver = ws_receiver
        self.agent_class = agent_class
        self.agent_id = agent_id

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
        AgentChatService.add_message_to_conversation(turn_context.activity.conversation.id, user_message)
        persisted_messages: List[Message] = AgentChatService.get_messages_by_conversation_id(
            turn_context.activity.conversation.id
        )
        messages: List[ChatMessage] = [
            AgentChatService.message_to_chat_message(message) for message in persisted_messages
        ]
        response: str = await AgentChatService.json_chat(
            user_id=turn_context.activity.from_property.id,
            agent_class=self.agent_class,
            agent_id=self.agent_id,
            messages=messages,
            nc=self.nc,
            ws_receiver=self.ws_receiver,
        )
        return await AgentChatService.respond_to_user(turn_context, turn_context.activity, response)
