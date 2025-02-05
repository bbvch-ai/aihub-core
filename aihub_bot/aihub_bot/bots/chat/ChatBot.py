import logging
from typing import List

from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount
from llama_index.core.base.llms.types import ChatMessage
from nats.aio.client import Client as NATS

from aihub_bot.persistence.chat.entities.ConversationEntity import Message, User
from aihub_bot.routes.chat.ChatService import ChatService
from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver

logger = logging.getLogger(__name__)


class ChatBot(ActivityHandler):
    """
    AI-powered chatbot that processes user messages and interacts with conversation history.
    Handles the interaction with the Azure Bot Service.

    ### Purpose
    - Captures user input and maintains a structured conversation.
    - Forwards user messages to an AI agent.
    - Stores and retrieves messages using `ConversationEntity`.
    - Supports both new and existing conversations.

    ### Workflow
    1. **Conversation Initialization**:
        - Creates a new conversation or retrieves an existing one.
        - Adds users to the conversation.
    2. **User Interaction**:
        - Persists user messages in the conversation history.
        - Sends user messages to the AI agent with the conversation history for context.
    3. **Agent Interaction**:
        - Persists agent responses in the conversation history.
        - Sends agent responses to the Azure Bot Service.
    """

    def __init__(self, nc: NATS, ws_receiver: WebSocketReceiver, agent_class: str, agent_id: str):
        self.nc = nc
        self.ws_receiver = ws_receiver
        self.agent_class = agent_class
        self.agent_id = agent_id

    async def on_conversation_update_activity(self, turn_context: TurnContext):
        """
        A conversation update activity is sent when a new conversation is started or a member is added to an existing conversation.

        Persists conversations in the database when a new conversation is started in order to store user and assistant messages.
        """
        ChatService.create_conversation(turn_context.activity.conversation.id, [], [])
        await super().on_conversation_update_activity(turn_context)

    async def on_members_added_activity(self, members_added: List[ChannelAccount], turn_context: TurnContext):
        """
        If members are added in a conversation update activity, this method is called.

        Adds new users to an existing conversation.
        TODO (When implementing this for the first customer): Handle custom welcome messages.
        """
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                user = User(user_id=member.id)
                ChatService.add_user_to_conversation(turn_context.activity.conversation.id, user)
                return await ChatService.respond_to_user(turn_context, turn_context.activity, "Hello and welcome!")

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
