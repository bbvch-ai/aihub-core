import asyncio
import logging
from typing import List
from dataclasses import dataclass

from bson import ObjectId
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


@dataclass
class StreamingResources:
    stop_event: asyncio.Event
    subscriber: NCSubscriber
    chunk_queue: asyncio.Queue


@dataclass
class JsonResources:
    stop_event: asyncio.Event
    subscriber: NCSubscriber
    chunk_events: List[ChunkEvent]
    costs: LLMCosts
    model_name: str

class ChatService:

    @staticmethod
    async def start_stream_chat_interaction(
        request_app_state,
        user: AuthenticatedUser,
        agent_class: str,
        agent_id: str,
        chat_completions_request: ChatCompletionsRequest,
    ) -> StreamingResources:
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

        topic_manager = AgentThreadTopicManager(
            agent_class=agent_class,
            agent_id=agent_id,
            thread_id=event.thread_id,
            display_id=event.display_id,
            run_id="*",
        )

        stop_event = asyncio.Event()
        chunk_queue = asyncio.Queue()

        async def response_aggregator(display_event: DisplayEvent, topic: AgentTopic):
            logger.debug(f"Received display event: {display_event}")
            if isinstance(display_event, ChunkEvent):
                logger.debug(f"Received chunk event: {display_event}")
                await chunk_queue.put(display_event)
            elif isinstance(display_event, StopEvent):
                logger.debug(f"Received stop event: {display_event}. Stop streaming")
                await subscriber.stop()
                stop_event.set()

        subscriber = NCSubscriber.for_thread_display_events(
            nc=request_app_state.nc,
            topic_manager=topic_manager,
            handler=response_aggregator,
        )

        await subscriber.start()
        logger.debug(f"Subscriber created for subject: {subscriber.subject}")

        ws_receiver = request_app_state.ws_receiver
        await ws_receiver.receive_event(event, user.oid)

        return StreamingResources(
            stop_event=stop_event,
            subscriber=subscriber,
            chunk_queue=chunk_queue
        )

    @staticmethod
    async def start_json_chat_interaction(
        request_app_state,
        user: AuthenticatedUser,
        agent_class: str,
        agent_id: str,
        chat_completions_request: ChatCompletionsRequest,
    ) -> JsonResources:
        # Create the thread
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

        topic_manager = AgentThreadTopicManager(
            agent_class=agent_class,
            agent_id=agent_id,
            thread_id=event.thread_id,
            display_id=event.display_id,
            run_id="*",
        )

        stop_event = asyncio.Event()
        chunk_events: List[ChunkEvent] = []
        costs = LLMCosts.from_zero()
        model_name = "bbv-ai-hub"

        # Create the resources object now, so aggregator can directly mutate it
        resources = JsonResources(
            stop_event=stop_event,
            subscriber=None,  # will assign after subscriber creation
            chunk_events=chunk_events,
            costs=costs,
            model_name=model_name
        )

        async def response_aggregator(display_event: DisplayEvent, topic: AgentTopic):
            logger.debug(f"Received display event: {display_event}")
            if isinstance(display_event, ChunkEvent):
                logger.debug(f"Received chunk event: {display_event}")
                resources.chunk_events.append(display_event)
            elif isinstance(display_event, StopEvent):
                logger.debug(f"Received stop event: {display_event}. Stop streaming")
                await resources.subscriber.stop()
                resources.stop_event.set()
            elif isinstance(display_event, LLMCostEvent):
                logger.debug(f"Received cost event: {display_event}")
                resources.costs += display_event
                resources.model_name = display_event.llm_name

        subscriber = NCSubscriber.for_thread_display_events(
            nc=request_app_state.nc,
            topic_manager=topic_manager,
            handler=response_aggregator,
        )
        resources.subscriber = subscriber

        await subscriber.start()
        logger.debug(f"Subscriber created for subject: {subscriber.subject}")

        ws_receiver = request_app_state.ws_receiver
        await ws_receiver.receive_event(event, user.oid)

        return resources

    @staticmethod
    def build_json_response(chunk_events: List[ChunkEvent], costs: LLMCosts, model_name: str) -> ChatCompletionsSuccessResponse:
        chunk_events = sorted(chunk_events, key=lambda x: x.created_at)
        content = ''.join([chunk.content for chunk in chunk_events])
        return ChatCompletionsSuccessResponse.from_string(content, costs, model=model_name)

    @staticmethod
    def create_sse_generator(stop_event: asyncio.Event, chunk_queue: asyncio.Queue):
        async def sse_event_generator():
            while True:
                if stop_event.is_set() and chunk_queue.empty():
                    logger.debug("Stop streaming due to stop_event and empty queue")
                    break
                try:
                    chunk_event = await asyncio.wait_for(chunk_queue.get(), timeout=0.5)
                    chat_completion_chunk = ChatCompletionChunk.from_string(
                        chunk_event.content,
                        model=chunk_event.model_name
                    )
                    yield f"data: {chat_completion_chunk.model_dump_json()}\n\n"
                    chunk_queue.task_done()
                except asyncio.TimeoutError:
                    logger.debug("Timeout waiting for chunk event. Continuing...")
                    continue
                except asyncio.CancelledError:
                    break
            # Send a final "stop" chunk
            chat_completion_chunk = ChatCompletionChunk.from_string("", model="", finish_reason="stop")
            yield f"data: {chat_completion_chunk.model_dump_json()}\n\n"

        return sse_event_generator()
