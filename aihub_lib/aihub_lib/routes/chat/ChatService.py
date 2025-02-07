import asyncio
import logging
from dataclasses import dataclass
from typing import List, Tuple

from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage
from nats.aio.client import Client as NATS

from aihub_lib.generative_ai.llms.costs.LLMCosts import LLMCosts
from aihub_lib.nats.events import ChunkEvent, DisplayEvent, StopEvent
from aihub_lib.nats.events.cost.LLMCostEvent import LLMCostEvent
from aihub_lib.nats.events.user import UserMessageEvent
from aihub_lib.nats.subscribers.NCSubscriber import NCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from aihub_lib.nats.topics.agents.AgentTopic import AgentTopic
from aihub_lib.persistence.messaging.entities.ThreadEntity import Agent, ThreadEntity, User
from aihub_lib.sockets.events.user_to_server.WSUserEvent import WSUserEvent
from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver

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
    """
    Orchestrates chat interactions for both streaming and JSON-based endpoints.
    """

    @staticmethod
    def _initialize_interaction(
        user_oid: str,
        agent_class: str,
        agent_id: str,
        messages: List[ChatMessage],
    ) -> Tuple[WSUserEvent, AgentThreadTopicManager]:
        """
        Common initialization steps for both streaming and JSON interactions.
        """
        thread = ThreadEntity.create_thread(
            "chat",
            users=[User(user_id=user_oid)],
            agents=[Agent(agent_class=agent_class, agent_id=agent_id)],
        )
        logger.debug(f"Created thread: {thread.id}")

        event = WSUserEvent(
            thread_id=str(thread.id),
            display_id=str(ObjectId()),
            event=UserMessageEvent(
                messages=messages,
            ),
        )
        logger.debug(f"Created event: {event}")

        topic_manager = AgentThreadTopicManager(
            agent_class=agent_class,
            agent_id=agent_id,
            thread_id=event.thread_id,
            display_id=event.display_id,
            run_id="*",
        )
        return event, topic_manager

    @staticmethod
    async def start_stream_chat_interaction(
        user_oid: str,
        agent_class: str,
        agent_id: str,
        messages: List[ChatMessage],
        nc: NATS,
        ws_receiver: WebSocketReceiver,
    ) -> StreamingResources:
        """
        Starts a streaming chat interaction and returns the resources for SSE streaming.
        """
        event, topic_manager = ChatService._initialize_interaction(user_oid, agent_class, agent_id, messages)

        stop_event = asyncio.Event()
        chunk_queue = asyncio.Queue()

        async def response_aggregator(display_event: DisplayEvent, topic: AgentTopic):
            logger.debug(f"Received display event: {display_event}")
            if isinstance(display_event, ChunkEvent):
                logger.debug(f"Received chunk event: {display_event}")
                await chunk_queue.put(display_event)
            elif isinstance(display_event, StopEvent):
                logger.debug("Received stop event. Stop streaming")
                await subscriber.stop()
                stop_event.set()

        subscriber = NCSubscriber.for_thread_display_events(
            nc=nc,
            topic_manager=topic_manager,
            handler=response_aggregator,
        )
        await subscriber.start()
        logger.debug(f"Subscriber created for subject: {subscriber.subject}")

        # Trigger the agent interaction via WebSocket
        await ws_receiver.receive_event(event, user_oid)

        return StreamingResources(stop_event=stop_event, subscriber=subscriber, chunk_queue=chunk_queue)

    @staticmethod
    async def start_json_chat_interaction(
        user_oid: str,
        agent_class: str,
        agent_id: str,
        messages: List[ChatMessage],
        nc: NATS,
        ws_receiver: WebSocketReceiver,
    ) -> JsonResources:
        """
        Starts a JSON-based chat interaction, waiting for all events before returning.
        """
        event, topic_manager = ChatService._initialize_interaction(user_oid, agent_class, agent_id, messages)

        stop_event = asyncio.Event()
        chunk_events: List[ChunkEvent] = []
        costs = LLMCosts.from_zero()
        model_name = "bbv-ai-hub"

        resources = JsonResources(
            stop_event=stop_event,
            subscriber=None,  # Will be set after subscriber creation.
            chunk_events=chunk_events,
            costs=costs,
            model_name=model_name,
        )

        async def response_aggregator(display_event: DisplayEvent, topic: AgentTopic):
            logger.debug(f"Received display event: {display_event}")
            if isinstance(display_event, ChunkEvent):
                resources.chunk_events.append(display_event)
            elif isinstance(display_event, StopEvent):
                logger.debug("Received stop event. Stop streaming")
                await resources.subscriber.stop()
                resources.stop_event.set()
            elif isinstance(display_event, LLMCostEvent):
                resources.costs += display_event
                resources.model_name = display_event.llm_name

        subscriber = NCSubscriber.for_thread_display_events(
            nc=nc,
            topic_manager=topic_manager,
            handler=response_aggregator,
        )
        resources.subscriber = subscriber

        await subscriber.start()
        logger.debug(f"Subscriber created for subject: {subscriber.subject}")

        # Trigger the agent interaction
        await ws_receiver.receive_event(event, user_oid)

        return resources

    @staticmethod
    def build_json_response_content(chunk_events: List[ChunkEvent]) -> str:
        """
        Construct a JSON response from collected chunk events.
        """
        sorted_chunks = sorted(chunk_events, key=lambda x: x.created_at)
        content = "".join(chunk.content for chunk in sorted_chunks)
        return content
