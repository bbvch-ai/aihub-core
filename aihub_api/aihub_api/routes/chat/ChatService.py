import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import List

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.generative_ai.resources.costs.LLMCosts import LLMCosts
from aihub_lib.nats.events import ChunkEvent
from aihub_lib.routes.chat.ChatService import ChatService as ChatServiceLib
from aihub_lib.routes.chat.ChatService import JsonResources, StreamingResources
from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver
from nats.aio.client import Client as NATS
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionChunk, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice as JsonChoice
from openai.types.chat.chat_completion_chunk import Choice, ChoiceDelta

from aihub_api.routes.openai.dto.ChatCompletionRequest import ChatCompletionRequest

logger = logging.getLogger(__name__)


class ChatService(ChatServiceLib):
    """
    Orchestrates chat interactions for both streaming and JSON-based endpoints.

    ### Key Steps in the Interaction
    1. Create a conversation thread (saving state in ThreadEntity).
    2. Convert user request into a WSUserEvent and send it to the agent via WebSocketReceiver.
    3. Subscribe to agent responses (via DisplayEvents) and aggregate them.
    4. For streaming:
       - Return an SSE stream of chunked responses as they are produced.
    5. For JSON:
       - Wait for all responses (chunks and cost events), then build a single JSON response.

    ### Separation of Concerns
    ChatService doesn't handle HTTP details directly. Instead, it:
    - Creates threads
    - Sends WSUserEvents to the system
    - Subscribes to events from agents
    - Aggregates results (chunks, costs)
    - Returns structured resources for controllers to send back to clients.

    This design ensures the service is testable and maintainable.
    """

    @staticmethod
    async def start_api_stream_chat_interaction(
        user: AuthenticatedUser,
        agent_class: str,
        agent_id: str,
        chat_completions_request: ChatCompletionRequest,
        nc: NATS,
        ws_receiver: WebSocketReceiver,
    ) -> StreamingResources:
        """
        Starts a streaming chat interaction. The final output is a SSE generator.

        Steps:
        1. Create a thread.
        2. Create and send a WSUserEvent with the user's messages.
        3. Subscribe to display events (ChunkEvents and StopEvent).
        4. Return resources containing a chunk_queue and a stop_event. The controller uses these to produce SSE.
        """
        return await ChatService.start_stream_chat_interaction(
            user_oid=user.oid,
            agent_class=agent_class,
            agent_id=agent_id,
            messages=chat_completions_request.messages,
            nc=nc,
            ws_receiver=ws_receiver,
        )

    @staticmethod
    async def start_api_json_chat_interaction(
        user: AuthenticatedUser,
        agent_class: str,
        agent_id: str,
        chat_completions_request: ChatCompletionRequest,
        nc: NATS,
        ws_receiver: WebSocketReceiver,
    ) -> JsonResources:
        """
        Starts a JSON-based chat interaction, waiting until all tokens and costs are processed before returning.

        Similar steps as the streaming method, but here we collect all ChunkEvents and LLMCostEvents,
        and wait for a StopEvent before constructing the final JSON response.
        """
        return await ChatService.start_json_chat_interaction(
            user_oid=user.oid,
            agent_class=agent_class,
            agent_id=agent_id,
            messages=chat_completions_request.messages,
            nc=nc,
            ws_receiver=ws_receiver,
        )

    @staticmethod
    def build_api_json_response(chunk_events: List[ChunkEvent], costs: LLMCosts, model_name: str) -> ChatCompletion:
        """
        Construct a JSON response from collected chunk events and cost metrics.

        Sort chunks by creation time, join them into a single string, and use `ChatCompletionsSuccessResponse`
        to wrap the content and usage data.
        """
        content = ChatService.build_json_response_content(chunk_events)
        return ChatCompletion(
            id=str(uuid.uuid4()),
            object="chat.completion",
            created=int(datetime.now(timezone.utc).timestamp()),
            model=model_name,
            choices=[
                JsonChoice(
                    index=0,
                    message=ChatCompletionMessage(role="assistant", content=content),
                    finish_reason="stop",
                )
            ],
            usage=CompletionUsage(
                prompt_tokens=costs.prompt_token_count,
                completion_tokens=costs.completion_token_count,
                total_tokens=(costs.prompt_token_count + costs.completion_token_count),
            ),
        )

    @staticmethod
    def create_api_sse_generator(stop_event: asyncio.Event, chunk_queue: asyncio.Queue):
        """
        Creates an asynchronous generator producing SSE events from a queue of ChunkEvents.

        When a chunk is available, it is converted into a `ChatCompletionChunk` and yielded.
        When stop_event is set and the queue is empty, the generator sends a final stop chunk and ends.
        """

        async def sse_event_generator():
            while True:
                if stop_event.is_set() and chunk_queue.empty():
                    logger.debug("Stop streaming due to stop_event and empty queue")
                    break
                try:
                    chunk_event = await asyncio.wait_for(chunk_queue.get(), timeout=0.5)
                    chat_completion_chunk = ChatCompletionChunk(
                        id=str(uuid.uuid4()),
                        object="chat.completion.chunk",
                        created=int(datetime.now(timezone.utc).timestamp()),
                        model=chunk_event.model_name,
                        choices=[Choice(index=0, delta=ChoiceDelta(content=chunk_event.content, role="assistant"))],
                        usage=None,
                    )
                    yield f"data: {chat_completion_chunk.model_dump_json()}\n\n"
                    chunk_queue.task_done()
                except asyncio.TimeoutError:
                    # No new chunk yet; keep waiting
                    continue
                except asyncio.CancelledError:
                    break
            # Send a final "stop" chunk at the end
            chat_completion_chunk = ChatCompletionChunk(
                id=str(uuid.uuid4()),
                object="chat.completion.chunk",
                created=int(datetime.now(timezone.utc).timestamp()),
                model="",
                choices=[Choice(index=0, delta=ChoiceDelta(content="", role="assistant"), finish_reason="stop")],
                usage=None,
            )
            yield f"data: {chat_completion_chunk.model_dump_json()}\n\n"

        return sse_event_generator()
