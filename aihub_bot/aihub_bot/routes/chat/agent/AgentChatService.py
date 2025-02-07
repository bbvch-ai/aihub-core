from typing import AsyncGenerator, List

from aihub_lib.routes.chat.ChatService import JsonResources, StreamingResources
from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver
from llama_index.core.base.llms.types import ChatMessage
from nats.aio.client import Client as NATS

from aihub_bot.routes.chat.ChatService import ChatService


class AgentChatService(ChatService):
    @staticmethod
    async def stream_chat(
        user_id: str,
        agent_class: str,
        agent_id: str,
        messages: List[ChatMessage],
        nc: NATS,
        ws_receiver: WebSocketReceiver,
    ) -> AsyncGenerator[str, None]:
        resources: StreamingResources = await AgentChatService.start_stream_chat_interaction(
            user_oid=user_id,
            agent_class=agent_class,
            agent_id=agent_id,
            messages=messages,
            nc=nc,
            ws_receiver=ws_receiver,
        )
        return AgentChatService.build_stream_response_generator(resources.stop_event, resources.chunk_queue)

    @staticmethod
    async def json_chat(
        user_id: str,
        agent_class: str,
        agent_id: str,
        messages: List[ChatMessage],
        nc: NATS,
        ws_receiver: WebSocketReceiver,
    ) -> str:
        """
        Processes a JSON-based chat request with an AI agent.

        ### Purpose
        - Manages a synchronous AI interaction where the user receives a response only after all processing is completed.

        ### Workflow
        1. Initiates a conversation between the user and the specified agent.
        2. Waits for AI-generated responses (including chunks and cost tracking events).
        3. Constructs a final JSON response after all events are received.
        """

        resources: JsonResources = await AgentChatService.start_json_chat_interaction(
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
        return AgentChatService.build_json_response_content(resources.chunk_events)
