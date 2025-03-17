import asyncio
from typing import AsyncGenerator, List, Optional

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.routes.chat.ChatService import JsonResources, StreamingResources
from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver
from botbuilder.core import TurnContext
from llama_index.core.base.llms.types import ChatMessage, ContentBlock, ImageBlock, MessageRole, TextBlock
from nats.aio.client import Client as NATS

from aihub_bot.persistence.entities.ConversationEntity import Content, Message
from aihub_bot.routes.Service import Service


class AgentChatService(Service):
    """
    ### What
    - Shared functionality for the AgentChatController and AgentChatBots.
    """

    @staticmethod
    async def json_chat_completion(
        turn_context: TurnContext,
        path: str,
        agent_class: str,
        agent_id: str,
        nc: NATS,
        ws_receiver: WebSocketReceiver,
        thread_id: Optional[str] = None,
    ) -> str:
        """
        ### What
        - Start a chat interaction with an Agent and return the response as a single string.

        ### Why
        - Send the response in one single message.
        - Some channels (e.g. webchat) do not support streaming.
        """
        resources: JsonResources = await AgentChatService.chat_completion(
            turn_context=turn_context,
            path=path,
            agent_class=agent_class,
            agent_id=agent_id,
            nc=nc,
            ws_receiver=ws_receiver,
            thread_id=thread_id,
            stream=False,
        )

        await resources.stop_signal.wait()
        await resources.subscriber.stop()

        return AgentChatService.build_json_response_content(resources.chunk_events, resources.stop_event)

    @staticmethod
    async def stream_chat_completion(
        turn_context: TurnContext,
        path: str,
        agent_class: str,
        agent_id: str,
        nc: NATS,
        ws_receiver: WebSocketReceiver,
        thread_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        ### What
        - Start a chat interaction with an Agent.
        - Return a generator that yields the response in chunks.

        ### Why
        - Send the response in multiple chunks by updating the message for each chunk.
        """
        resources: StreamingResources = await AgentChatService.chat_completion(
            turn_context=turn_context,
            path=path,
            agent_class=agent_class,
            agent_id=agent_id,
            nc=nc,
            ws_receiver=ws_receiver,
            thread_id=thread_id,
            stream=True,
        )

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
        ws_receiver: WebSocketReceiver,
        thread_id: Optional[str] = None,
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
        persisted_messages: List[Message] = Service.get_messages_by_conversation_id(
            conversation_id=turn_context.activity.conversation.id
        )
        system_message: Message = Service.get_system_message(
            turn_context=turn_context,
            path=path,
        )
        if system_message is not None:
            persisted_messages.insert(0, system_message)
        chat_messages: List[ChatMessage] = [
            AgentChatService._message_to_chat_message(message) for message in persisted_messages
        ]
        user = AuthenticatedUser(
            name=turn_context.activity.from_property.name,
            preferred_username=turn_context.activity.from_property.name,
            oid=turn_context.activity.from_property.id,
            roles=[],
        )
        if stream:
            return await Service.start_stream_chat_interaction(
                user=user,
                agent_class=agent_class,
                agent_id=agent_id,
                messages=chat_messages,
                nc=nc,
                ws_receiver=ws_receiver,
                thread_id=thread_id,
            )
        else:
            return await Service.start_json_chat_interaction(
                user=user,
                agent_class=agent_class,
                agent_id=agent_id,
                messages=chat_messages,
                nc=nc,
                ws_receiver=ws_receiver,
                thread_id=thread_id,
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
            content=[AgentChatService._content_to_content_block(content) for content in message.content],
            name=message.name,
        )

    @staticmethod
    def _content_to_content_block(content: Content) -> ContentBlock:
        match content.type:
            case "text":
                return TextBlock(text=content.text, block_type="text")
            case "image_url":
                return ImageBlock(url=content.text, block_type="image")
