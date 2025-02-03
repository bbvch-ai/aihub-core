import asyncio
import logging
from dataclasses import dataclass
from typing import List

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
    """
    Holds resources required for streaming responses:
    - stop_event: Signals when streaming should end.
    - subscriber: Subscribed to display events that provide chunks.
    - chunk_queue: Queue of chunks waiting to be sent as SSE.
    """

    stop_event: asyncio.Event
    subscriber: NCSubscriber
    chunk_queue: asyncio.Queue


@dataclass
class JsonResources:
    """
    Holds resources for JSON-based responses:
    - stop_event: Signals when the run is complete.
    - subscriber: Subscribed to display events.
    - chunk_events: Accumulated chunk events for constructing the final response.
    - costs: Tracks LLMCostEvents for usage reporting.
    - model_name: Tracks the LLM model name used.
    """

    stop_event: asyncio.Event
    subscriber: NCSubscriber
    chunk_events: List[ChunkEvent]
    costs: LLMCosts
    model_name: str


class ChatService:
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
    async def start_stream_chat_interaction(
        user_oid: str,
        agent_class: str,
        agent_id: str,
        messages: List[ChatMessage],
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
                messages=messages[:-1],
                content=messages[-1].content,
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
        Starts a JSON-based chat interaction, waiting until all tokens and costs are processed before returning.

        Similar steps as the streaming method, but here we collect all ChunkEvents and LLMCostEvents,
        and wait for a StopEvent before constructing the final JSON response.
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
                messages=messages[:-1],
                content=messages[-1].content,
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

        stop_event = asyncio.Event()
        chunk_events: List[ChunkEvent] = []
        costs = LLMCosts.from_zero()
        model_name = "bbv-ai-hub"

        resources = JsonResources(
            stop_event=stop_event,
            subscriber=None,  # assigned after subscriber creation
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
        Construct a JSON response from collected chunk events and cost metrics.

        Sort chunks by creation time, join them into a single string, and use `ChatCompletionsSuccessResponse`
        to wrap the content and usage data.
        """
        chunk_events = sorted(chunk_events, key=lambda x: x.created_at)
        content = "".join([chunk.content for chunk in chunk_events])
        return content
