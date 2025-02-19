import asyncio
from typing import AsyncGenerator, List

from botbuilder.core import TurnContext
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from nats.aio.client import Client as NATS

from aihub_bot.persistence.entities.ConversationEntity import Message
from aihub_bot.routes.Service import Service
from aihub_lib.routes.chat.ChatService import JsonResources, StreamingResources
from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver


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
            stream=False,
        )

        await resources.stop_event.wait()
        await resources.subscriber.stop()

        return AgentChatService.build_json_response_content(resources.chunk_events)

    @staticmethod
    async def stream_chat_completion(
        turn_context: TurnContext,
        path: str,
        agent_class: str,
        agent_id: str,
        nc: NATS,
        ws_receiver: WebSocketReceiver,
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
            stream=True,
        )

        async def response_generator():
            while True:
                if resources.stop_event.is_set() and resources.chunk_queue.empty():
                    break
                chunk_event = await asyncio.wait_for(resources.chunk_queue.get(), timeout=30)
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
            AgentChatService.message_to_chat_message(message) for message in persisted_messages
        ]
        if stream:
            return await Service.start_stream_chat_interaction(
                user_oid=turn_context.activity.from_property.id,
                agent_class=agent_class,
                agent_id=agent_id,
                messages=chat_messages,
                nc=nc,
                ws_receiver=ws_receiver,
            )
        else:
            return await Service.start_json_chat_interaction(
                user_oid=turn_context.activity.from_property.id,
                agent_class=agent_class,
                agent_id=agent_id,
                messages=chat_messages,
                nc=nc,
                ws_receiver=ws_receiver,
            )

    @staticmethod
    def message_to_chat_message(message: Message) -> ChatMessage:
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

        return ChatMessage(role=role, content=message.content)
