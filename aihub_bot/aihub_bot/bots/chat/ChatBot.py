from typing import List

from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount
from typing_extensions import override

from aihub_bot.persistence.entities.ConversationEntity import User
from aihub_bot.routes.chat.ChatService import ChatService


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

    @override
    async def on_conversation_update_activity(self, turn_context: TurnContext):
        """
        A conversation update activity is sent when a new conversation is started or a member is added to an existing conversation.

        Persists conversations in the database when a new conversation is started in order to store user and assistant messages.
        """
        ChatService.create_conversation(turn_context.activity.conversation.id, [], [])
        await super().on_conversation_update_activity(turn_context)

    @override
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
