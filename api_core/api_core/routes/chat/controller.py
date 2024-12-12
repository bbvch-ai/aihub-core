import asyncio
import logging
from typing import Callable, Any, List

from bson import ObjectId
from fastapi import APIRouter, Body, Path, Depends, Request
from starlette.responses import StreamingResponse

from api_core.auth.AuthenticatedUser import AuthenticatedUser
from api_core.routes.chat.dto.ChatCompletionsRequest import ChatCompletionsRequest
from api_core.routes.chat.dto.json.ChatCompletionsSuccessResponse import ChatCompletionsSuccessResponse
from api_core.routes.chat.dto.stream.ChatCompletionChunk import ChatCompletionChunk
from api_core.sockets.events.user_to_server.WSUserEvent import WSUserEvent
from lib_core.generative_ai.llms.costs.LLMCosts import LLMCosts
from lib_core.nats.events import ChunkEvent, DisplayEvent, StopEvent
from lib_core.nats.events.cost.LLMCostEvent import LLMCostEvent
from lib_core.nats.events.user import UserMessageEvent
from lib_core.nats.subscribers.NCSubscriber import NCSubscriber
from lib_core.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from lib_core.nats.topics.agents.AgentTopic import AgentTopic
from lib_core.persistence.messaging.entities.ThreadEntity import ThreadEntity, User, Agent

logger = logging.getLogger(__name__)

def chat_controller_factory(user_auth_strategy:  Callable[..., Any]):

    chat_router = APIRouter()

    @chat_router.post(
        "/completions/{agent_class}/{agent_id}/stream",
        summary="Stream Chat",
        description="Initiates a streaming interaction with a specific agent. This endpoint requires authentication, checks user roles and spending limits, and supports file uploads.",
        tags=["Agent"],
        responses={
            200: {
                "description": "Successful streaming response",
                "content": {
                    "text/event-stream": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "object": {
                                    "type": "string",
                                    "enum": ["chat.completion.chunk"],
                                },
                                "created": {"type": "integer"},
                                "model": {"type": "string"},
                                "choices": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "index": {"type": "integer"},
                                            "finish_reason": {
                                                "type": "string",
                                                "nullable": True,
                                            },
                                            "delta": {
                                                "type": "object",
                                                "properties": {
                                                    "role": {
                                                        "type": "string",
                                                        "nullable": True,
                                                    },
                                                    "content": {"type": "string"},
                                                },
                                            },
                                        },
                                    },
                                },
                                "usage": {"type": "object", "nullable": True},
                            },
                        },
                        "example": """
    data: {"id":"chatcmpl-123abc","object":"chat.completion.chunk","created":1677858242,"model":"gpt-3.5-turbo-0613","choices":[{"index":0,"finish_reason":null,"delta":{"role":"assistant","content":"Hello"}}],"usage":null}
    data: {"id":"chatcmpl-123abc","object":"chat.completion.chunk","created":1677858242,"model":"gpt-3.5-turbo-0613","choices":[{"index":0,"finish_reason":null,"delta":{"content":", how can I assist you today?"}}],"usage":null}
    data: {"id":"chatcmpl-123abc","object":"chat.completion.chunk","created":1677858242,"model":"gpt-3.5-turbo-0613","choices":[{"index":0,"finish_reason":"stop","delta":{}}],"usage":{"prompt_tokens":20,"completion_tokens":15,"total_tokens":35}}
    """,
                        "description": "A stream of server-sent events. Each event is prefixed with 'data: ' and separated by two newline characters. The content of each event is a JSON object representing a chat completion chunk.",
                    }
                },
            },
            401: {"description": "Unauthorized access"},
            403: {"description": "Forbidden - user lacks appropriate access or has exceeded spending limits"},
            404: {"description": "Organization or agent not found"},
        },
        response_class=StreamingResponse,
    )
    async def stream_chat(
            request: Request,
            chat_completions_request: ChatCompletionsRequest = Body(
                ...,
                description="The chat completion request details",
            ),
            agent_class: str = Path(
                ...,
                description="Class that implements the agents functionality",
            ),
            agent_id: str = Path(
                ...,
                description="Agent ID that was given to the microservice running the agent",
            ),
            user: AuthenticatedUser = Depends(user_auth_strategy),
    ) -> StreamingResponse:
        thread = ThreadEntity.create_thread(
            "chat",
            users=[User(user_id=user.oid)],
            agents=[Agent(agent_class=agent_class, agent_id=agent_id)],
        )
        logger.debug(f"Created thread: {thread.id}")

        messages = chat_completions_request.messages

        event = WSUserEvent(
            thread_id=str(thread.id),
            display_id=str(ObjectId()),
            event=UserMessageEvent(
                messages=messages[:-1],
                content=messages[-1].content,
            )
        )
        logger.debug(f"Created event: {event}")

        stop_streaming = asyncio.Event()

        # Queue for received chunk events
        chunk_queue = asyncio.Queue()

        # Event for signaling that we should stop streaming
        stop_streaming = asyncio.Event()

        async def response_aggregator(event: DisplayEvent, topic: AgentTopic):
            logger.debug(f"Received display event: {event}")
            if isinstance(event, ChunkEvent):
                logger.debug(f"Received chunk event: {event}")
                await chunk_queue.put(event)
            elif isinstance(event, StopEvent):
                logger.debug(f"Received stop event: {event}. Stop streaming")
                await subscriber.stop()
                stop_streaming.set()

        subscriber = NCSubscriber.for_thread_display_events(
            nc=request.app.state.nc,
            topic_manager=AgentThreadTopicManager(
                agent_class=agent_class,
                agent_id=agent_id,
                thread_id=event.thread_id,
                display_id=event.display_id,
                run_id="*",
            ),
            handler=response_aggregator,
        )

        logger.debug(f"Subscriber created for subject: {subscriber.subject}")
        await subscriber.start()

        ws_receiver = request.app.state.ws_receiver
        await ws_receiver.receive_event(event, user.oid)

        async def sse_event_generator():
            # Keep streaming until stop_event is set and all chunks are processed
            while True:
                # If stop_event is set and queue is empty, break the loop
                if stop_streaming.is_set() and chunk_queue.empty():
                    logger.debug("Stop streaming due to stop_streaming flag and empty queue")
                    break

                try:
                    # Wait for a chunk event
                    chunk_event = await asyncio.wait_for(chunk_queue.get(), timeout=0.5)
                    # Format SSE message:
                    # SSE requires messages to start with "data:" and end with "\n\n"
                    chat_completion_chunk = ChatCompletionChunk.from_string(chunk_event.content, model=chunk_event.model_name)
                    yield f"data: {chat_completion_chunk.model_dump_json()}\n\n"
                    chunk_queue.task_done()
                except asyncio.TimeoutError:
                    logger.debug("Timeout waiting for chunk event. Continue streaming")
                    continue
                except asyncio.CancelledError:
                    # Handle cancellation if client disconnects or server shuts down
                    break
                chat_completion_chunk = ChatCompletionChunk.from_string("", model="", finish_reason="stop")
                yield f"data: {chat_completion_chunk.model_dump_json()}\n\n"

        # Return a streaming response that yields events as they arrive
        return StreamingResponse(sse_event_generator(), media_type="text/event-stream")


    @chat_router.post(
        "/completions/{agent_class}/{agent_id}/json",
        description="Initiates an interaction with a specific agent and returns a JSON response. This endpoint requires authentication, checks user roles and spending limits, and supports file uploads.",
        tags=["Agent"],
        responses={
            200: {"description": "Successful response with chat completion data"},
            401: {"description": "Unauthorized access"},
            403: {"description": "Forbidden - user lacks appropriate access or has exceeded spending limits"},
            404: {"description": "Organization or agent not found"},
        },
    )
    async def json_chat(
            request: Request,
            chat_completions_request: ChatCompletionsRequest = Body(
                ...,
                description="The chat completion request details",
            ),
            agent_class: str = Path(
                ...,
                description="Class that implements the agents functionality",
            ),
            agent_id: str = Path(
                ...,
                description="Agent ID that was given to the microservice running the agent",
            ),
            user: AuthenticatedUser = Depends(user_auth_strategy),
    ) -> ChatCompletionsSuccessResponse:
        thread = ThreadEntity.create_thread(
            "chat",
            users=[User(user_id=user.oid)],
            agents=[Agent(agent_class=agent_class, agent_id=agent_id)],
        )
        logger.debug(f"Created thread: {thread.id}")

        messages = chat_completions_request.messages

        event = WSUserEvent(
            thread_id=str(thread.id),
            display_id=str(ObjectId()),
            event=UserMessageEvent(
                messages=messages[:-1],
                content=messages[-1].content,
            )
        )
        logger.debug(f"Created event: {event}")

        model_name = "bbv-ai-hub"
        chunk_events: List[ChunkEvent] = []
        costs = LLMCosts.from_zero()
        stop_event = asyncio.Event()

        async def response_aggregator(event: DisplayEvent, topic: AgentTopic):
            logger.debug(f"Received display event: {event}")
            if isinstance(event, ChunkEvent):
                logger.debug(f"Received chunk event: {event}")
                chunk_events.append(event)
            elif isinstance(event, StopEvent):
                logger.debug(f"Received stop event: {event}. Stop streaming")
                await subscriber.stop()
                stop_event.set()
            elif isinstance(event, LLMCostEvent):
                logger.debug(f"Received cost event: {event}")
                nonlocal costs
                costs += event
                nonlocal model_name
                model_name = event.llm_name

        subscriber = NCSubscriber.for_thread_display_events(
            nc=request.app.state.nc,
            topic_manager=AgentThreadTopicManager(
                agent_class=agent_class,
                agent_id=agent_id,
                thread_id=event.thread_id,
                display_id=event.display_id,
                run_id="*",
            ),
            handler=response_aggregator,
        )

        await subscriber.start()
        logger.debug(f"Subscriber created for subject: {subscriber.subject}")

        ws_receiver = request.app.state.ws_receiver
        await ws_receiver.receive_event(event, user.oid)

        await stop_event.wait()
        await subscriber.stop()

        chunk_events = sorted(chunk_events, key=lambda x: x.created_at)
        content = ''.join([chunk.content for chunk in chunk_events])
        return ChatCompletionsSuccessResponse.from_string(content, costs, model=model_name)

    return chat_router