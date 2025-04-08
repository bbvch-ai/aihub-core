import asyncio
from typing import AsyncGenerator, List, Optional

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.nats.distributor.ExternalEventDistributor import ExternalEventDistributor
from aihub_lib.nats.events import ExceptionEvent
from aihub_lib.routes.chat.ChatService import ChatService, JsonResources, StreamingResources
from botbuilder.core import TurnContext
from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage, ContentBlock, ImageBlock, MessageRole, TextBlock
from nats.aio.client import Client as NATS

from aihub_bot.bots.BaseChatBot import CompletionHandler
from aihub_bot.persistence.entities.ConversationEntity import Content, Message


class AgentCompletionHandler(CompletionHandler):
    """
    Strategy for handling Agent completions.
    """

    @staticmethod
    async def get_completion(
        turn_context: TurnContext,
        path: str,
        agent_class: str,
        agent_id: str,
        nc: NATS,
        external_event_distributor: ExternalEventDistributor,
        thread_id: Optional[ObjectId] = None,
        display_id: Optional[ObjectId] = None,
        **kwargs,
    ) -> str:
        """Get a non-streaming Agent completion."""
        resources: JsonResources = await AgentCompletionHandler.chat_completion(
            turn_context=turn_context,
            path=path,
            agent_class=agent_class,
            agent_id=agent_id,
            nc=nc,
            external_event_distributor=external_event_distributor,
            thread_id=thread_id,
            display_id=display_id,
            stream=False,
        )

        if isinstance(resources.stop_event, ExceptionEvent):
            raise RuntimeError(resources.stop_event.message)

        await resources.stop_signal.wait()
        await resources.subscriber.stop()

        chat_content = ChatService.build_json_response_content(resources.chunk_events, resources.stop_event)
        return chat_content.content

    @staticmethod
    async def get_stream_completion(
        turn_context: TurnContext,
        path: str,
        agent_class: str,
        agent_id: str,
        nc: NATS,
        external_event_distributor: ExternalEventDistributor,
        thread_id: Optional[ObjectId] = None,
        display_id: Optional[ObjectId] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Get a streaming Agent completion."""
        resources: StreamingResources = await AgentCompletionHandler.chat_completion(
            turn_context=turn_context,
            path=path,
            agent_class=agent_class,
            agent_id=agent_id,
            nc=nc,
            external_event_distributor=external_event_distributor,
            thread_id=thread_id,
            display_id=thread_id,
            stream=True,
        )

        if isinstance(resources.stop_event, ExceptionEvent):
            raise RuntimeError(resources.stop_event.message)

        async def response_generator():
            while True:
                if resources.stop_signal.is_set() and resources.chunk_queue.empty():
                    break
                try:
                    chunk_event = await asyncio.wait_for(resources.chunk_queue.get(), timeout=30)
                except TimeoutError as e:
                    if resources.stop_signal.is_set():
                        break
                    raise e

                yield chunk_event.content
                resources.chunk_queue.task_done()

        return response_generator()

    @staticmethod
    async def chat_completion(
        turn_context: TurnContext,
        path: str,
        agent_class: str,
        agent_id: str,
        nc: NATS,
        external_event_distributor: ExternalEventDistributor,
        thread_id: Optional[ObjectId] = None,
        display_id: Optional[ObjectId] = None,
        stream: bool = False,
    ) -> StreamingResources | JsonResources:
        """
        ### What
        - Fetch persisted messages from the database.
        - Convert the messages to the correct format.
        - Start a chat interaction with the Agent.

        ### Why
        - The messages must be converted to the correct format to send them to the Agent.
        - The context is needed to generate the completion.
        """
        persisted_messages: List[Message] = CompletionHandler.get_messages_by_conversation_id(
            conversation_id=turn_context.activity.conversation.id
        )
        system_message: Message = CompletionHandler.get_system_message(
            turn_context=turn_context,
            path=path,
        )
        if system_message is not None:
            persisted_messages.insert(0, system_message)
        chat_messages: List[ChatMessage] = [
            AgentCompletionHandler._message_to_chat_message(message) for message in persisted_messages
        ]
        user = AuthenticatedUser(
            name=turn_context.activity.from_property.name,
            preferred_username=turn_context.activity.from_property.name,
            oid=turn_context.activity.from_property.id,
            roles=[],
        )
        if stream:
            return await ChatService.start_stream_chat_interaction(
                user=user,
                agent_class=agent_class,
                agent_id=agent_id,
                messages=chat_messages,
                nc=nc,
                external_event_distributor=external_event_distributor,
                thread_id=thread_id,
                display_id=display_id,
            )
        else:
            return await ChatService.start_json_chat_interaction(
                user=user,
                agent_class=agent_class,
                agent_id=agent_id,
                messages=chat_messages,
                nc=nc,
                external_event_distributor=external_event_distributor,
                thread_id=thread_id,
                display_id=display_id,
            )

    @staticmethod
    def _message_to_chat_message(message: Message) -> ChatMessage:
        """
        ### What
        - Convert a message to a `ChatMessage`.

        ### Why
        - The message must be converted to the correct format to send it to the Agent.
        """
        role: MessageRole
        match message.role:
            case "user":
                role = MessageRole.USER
            case "bot":
                role = MessageRole.ASSISTANT
            case "system":
                role = MessageRole.SYSTEM
            case _:
                raise NotImplementedError(f"Role {message.role} not supported")

        return ChatMessage(
            role=role,
            content=[AgentCompletionHandler._content_to_content_block(content) for content in message.content],
            name=message.name,
        )

    @staticmethod
    def _content_to_content_block(content: Content) -> ContentBlock:
        match content.type:
            case "text":
                return TextBlock(text=content.text, block_type="text")
            case "image_url":
                return ImageBlock(url=content.text, block_type="image")
