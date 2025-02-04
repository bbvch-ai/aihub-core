from typing import List

from llama_index.core.base.llms.types import ChatMessage
from nats.aio.client import Client as NATS

from aihub_bot.persistence.chat.entities.ConversationEntity import ConversationEntity, Message, User
from aihub_bot.routes.Service import Service
from aihub_lib.routes.chat.ChatService import ChatService as ChatServiceLib
from aihub_lib.routes.chat.ChatService import JsonResources
from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver


class ChatService(Service, ChatServiceLib):

    @staticmethod
    async def json_chat(
        user_id: str,
        agent_class: str,
        agent_id: str,
        messages: List[ChatMessage],
        nc: NATS,
        ws_receiver: WebSocketReceiver,
    ) -> str:
        resources: JsonResources = await ChatService.start_json_chat_interaction(
            user_oid=user_id,
            agent_class=agent_class,
            agent_id=agent_id,
            messages=messages,
            nc=nc,
            ws_receiver=ws_receiver,
        )

        # Wait until all events are processed
        await resources.stop_event.wait()
        await resources.subscriber.stop()

        # Construct final JSON response
        return ChatService.build_json_response_content(resources.chunk_events)

    @staticmethod
    def create_conversation(
        conversation_id: str,
        users: List[User],
        messages: List[Message],
    ) -> ConversationEntity:
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
