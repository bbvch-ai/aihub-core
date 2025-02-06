from typing import AsyncGenerator, List

from llama_index.core.base.llms.types import ChatMessage
from nats.aio.client import Client as NATS

from aihub_bot.routes.chat.ChatService import ChatService
from aihub_lib.routes.chat.ChatService import JsonResources, StreamingResources
from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver


class ChatAgentService(ChatService):
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
    async def stream_chat(
        user_id: str,
        agent_class: str,
        agent_id: str,
        messages: List[ChatMessage],
        nc: NATS,
        ws_receiver: WebSocketReceiver,
    ) -> AsyncGenerator[str, None]:
        resources: StreamingResources = await ChatAgentService.start_stream_chat_interaction(
            user_oid=user_id,
            agent_class=agent_class,
            agent_id=agent_id,
            messages=messages,
            nc=nc,
            ws_receiver=ws_receiver,
        )
        return ChatAgentService.build_stream_response_generator(resources.stop_event, resources.chunk_queue)

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

        resources: JsonResources = await ChatAgentService.start_json_chat_interaction(
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
        return ChatAgentService.build_json_response_content(resources.chunk_events)
