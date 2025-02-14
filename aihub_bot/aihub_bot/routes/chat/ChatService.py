import asyncio
from typing import AsyncGenerator, List

from botbuilder.core import TurnContext
from botbuilder.schema import Activity
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_bot.persistence.entities.ConversationEntity import ConversationEntity, Message, User
from aihub_bot.routes.Service import Service
from aihub_lib.routes.chat.ChatService import ChatService as ChatServiceLib


class ChatService(Service, ChatServiceLib):
    """
    Manages AI-driven chat interactions by orchestrating request handling and response generation.

    ### Purpose
    - Aggregates AI responses from WebSocket events.
    - Manages and persists conversation history.

    ### Workflow
    1. **User Request Handling**:
       - Receives and processes chat messages from Azure Bot Service.
       - Converts requests into structured agent interactions.
    2. **Agent Interaction**:
       - Sends WebSocket events to AI agents.
       - Collects responses from agents as they process the user input.
    3. **Conversation History**:
       - Stores and retrieves conversation history for each conversation.
       - Sends history to agents for context.
    4. **Response Aggregation**:
       - For JSON: Waits for all response chunks before compiling a final structured response.

    ### Integration
    - Provides the logic for the ChatBot to handle user interactions.
    - Communicates with AI agents via `WebSocketReceiver`.
    - Stores and retrieves conversation history via `ConversationEntity`.
    """

    @staticmethod
    def build_stream_response_generator(
        stop_event: asyncio.Event,
        chunk_queue: asyncio.Queue,
    ) -> AsyncGenerator[str, None]:
        async def response_generator():
            while True:
                if stop_event.is_set() and chunk_queue.empty():
                    break
                chunk_event = await asyncio.wait_for(chunk_queue.get(), timeout=1)
                yield chunk_event.content
                chunk_queue.task_done()

        return response_generator()

    @staticmethod
    def message_to_chat_message(message: Message) -> ChatMessage:
        """
        Azure Bot Service messages are stored as `Message` objects in the database.
        To communicate with AI agents, these messages must be converted to the llama-index `ChatMessage` format.
        """
        role: MessageRole
        match message.role:
            case "user":
                role = MessageRole.USER
            case "bot":
                role = MessageRole.ASSISTANT
            case _:
                raise NotImplementedError(f"Role {message.role} not supported")

        return ChatMessage(role=role, content=message.content)

    @staticmethod
    def create_conversation(
        conversation_id: str,
        users: List[User],
        messages: List[Message],
    ) -> ConversationEntity:
        """
        Conversations are persisted, such that we can track the history of messages and send them to agents for context.
        """
        existing = ConversationEntity.get_conversation_by_conversation_id(conversation_id)
        if existing is not None:
            return existing
        else:
            return ConversationEntity.create_conversation(
                conversation_id=conversation_id,
                users=users,
                messages=messages,
            )

    @staticmethod
    def add_user_to_conversation(
        conversation_id: str,
        user: User,
    ) -> ConversationEntity:
        return ConversationEntity.add_user_to_conversation(
            conversation_id=conversation_id,
            user=user,
        )

    @staticmethod
    def add_message_to_conversation(
        conversation_id: str,
        message: Message,
    ) -> ConversationEntity:
        return ConversationEntity.add_message_to_conversation(
            conversation_id=conversation_id,
            message=message,
        )

    @staticmethod
    def get_messages_by_conversation_id(
        conversation_id: str,
    ) -> List[Message]:
        return ConversationEntity.get_messages_by_conversation_id(conversation_id)

    @staticmethod
    async def respond_to_user(
        turn_context: TurnContext,
        user_activity: Activity,
        message: str,
    ):
        """
        As well as the user messages, we also persist the bot messages in the conversation history.
        """
        await turn_context.send_activity(message)
        bot_message: Message = Message(
            user_id=user_activity.recipient.id,
            content=message,
            role=user_activity.recipient.role or "bot",
        )
        ChatService.add_message_to_conversation(user_activity.conversation.id, bot_message)
