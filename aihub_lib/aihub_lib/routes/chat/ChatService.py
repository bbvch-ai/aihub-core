import asyncio
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple, Annotated

import mongoengine.errors
from bson import ObjectId
from fastapi import HTTPException
from llama_index.core.base.llms.types import ChatMessage
from nats.aio.client import Client as NATS

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.generative_ai.resources.costs.LLMCosts import LLMCosts
from aihub_lib.nats.events import (
    ChunkEvent,
    DisplayEvent,
    HumanInTheLoopRequestEvent,
    HumanInTheLoopResponseEvent,
    StopEvent,
)
from aihub_lib.nats.events.cost.LLMCostEvent import LLMCostEvent
from aihub_lib.nats.events.user import UserMessageEvent
from aihub_lib.nats.subscribers.NCSubscriber import NCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from aihub_lib.nats.topics.agents.AgentTopic import AgentTopic
from aihub_lib.persistence.messaging.entities.PersistedEventEntity import PersistedEventEntity
from aihub_lib.persistence.messaging.entities.ThreadEntity import Agent, ThreadEntity, User
from aihub_lib.sockets.events.user_to_server.WSUserEvent import WSUserEvent
from aihub_lib.sockets.receiver.WebSocketReceiver import WebSocketReceiver

logger = logging.getLogger(__name__)


@dataclass
class StreamingResources:
    stop_signal: asyncio.Event
    subscriber: NCSubscriber
    chunk_queue: asyncio.Queue
    stop_event: Optional[StopEvent | HumanInTheLoopRequestEvent] = None  # Added field to store the final StopEvent


@dataclass
class JsonResources:
    stop_signal: asyncio.Event
    subscriber: NCSubscriber
    chunk_events: List[ChunkEvent]
    costs: LLMCosts
    model_name: str
    stop_event: Optional[StopEvent | HumanInTheLoopRequestEvent] = None  # Added field to store the final StopEvent


class ChatService:
    """
    Orchestrates chat interactions for both streaming and JSON-based endpoints.
    """

    @staticmethod
    def _initialize_interaction(
        user: AuthenticatedUser,
        agent_class: str,
        agent_id: str,
        messages: List[ChatMessage],
        thread_id: Optional[str] = None,
        subscribe_to_thread: Annotated[bool, "Receive all events in thread, not just the ones from the specified agents"] = False
    ) -> Tuple[WSUserEvent, AgentThreadTopicManager]:
        """
        Common initialization steps for both streaming and JSON interactions.
        """
        thread = None
        if thread_id:
            try:
                thread = ThreadEntity.get_thread_by_id(thread_id)
                if not thread:
                    raise mongoengine.errors.DoesNotExist()
                if user.oid not in [u.user_id for u in thread.users]:
                    raise HTTPException(status_code=403, detail="User not part of the thread")
            except mongoengine.errors.DoesNotExist:
                pass
        if not thread:
            thread = ThreadEntity.create_thread(
                "chat",
                users=[User(user_id=user.oid)],
                agents=[Agent(agent_class=agent_class, agent_id=agent_id)],
                thread_id=ObjectId(thread_id) or ObjectId(),
            )
        logger.debug(f"Created thread: {thread.id}")

        hitl_requests = PersistedEventEntity.human_in_the_loop_request_events_for_thread(str(thread.id))
        hitl_responses = PersistedEventEntity.human_in_the_loop_response_events_for_thread(str(thread.id))

        thread_id = str(thread.id)
        display_id = str(ObjectId())

        if len(hitl_requests) != len(hitl_responses):
            open_hitl_request = hitl_requests[-1]
            event = HumanInTheLoopResponseEvent(
                response=messages[-1]["content"],
                request_event=HumanInTheLoopRequestEvent(**open_hitl_request.event_data),
            )
            display_id = event.request_event.topic.display_id
        else:
            event = UserMessageEvent(
                messages=messages,
                user=user,
            )

        event = WSUserEvent(
            thread_id=thread_id,
            display_id=display_id,
            event=event,
        )
        logger.debug(f"Created event: {event}")

        topic_manager = AgentThreadTopicManager(
            agent_class="*" if subscribe_to_thread else agent_class,
            agent_id="*" if subscribe_to_thread else agent_id,
            thread_id=event.thread_id,
            display_id=event.display_id,
            run_id="*",
        )
        return event, topic_manager

    @staticmethod
    async def start_stream_chat_interaction(
        user: AuthenticatedUser,
        agent_class: str,
        agent_id: str,
        messages: List[ChatMessage],
        nc: NATS,
        ws_receiver: WebSocketReceiver,
        thread_id: Optional[str] = None,
    ) -> StreamingResources:
        """
        Starts a streaming chat interaction and returns the resources for SSE streaming.
        """
        ws_event, topic_manager = ChatService._initialize_interaction(
            user=user,
            agent_class=agent_class,
            agent_id=agent_id,
            messages=messages,
            thread_id=thread_id,
            subscribe_to_thread=True,
        )

        stop_signal = asyncio.Event()
        chunk_queue = asyncio.Queue()
        resources = StreamingResources(
            stop_signal=stop_signal,
            subscriber=None,  # Will be set after subscriber creation
            chunk_queue=chunk_queue,
            stop_event=None,
        )

        async def response_aggregator(display_event: DisplayEvent, topic: AgentTopic):
            is_primary_agent = topic.agent_class == agent_class and topic.agent_id == agent_id
            logger.debug(f"Received display event: {display_event}")
            if isinstance(display_event, ChunkEvent):
                logger.debug(f"Received chunk event: {display_event}")
                await chunk_queue.put(display_event)
            elif isinstance(display_event, HumanInTheLoopRequestEvent):
                resources.stop_event = display_event
                await subscriber.stop()
                stop_signal.set()
            elif isinstance(display_event, StopEvent) and is_primary_agent:
                logger.debug("Received stop event. Stop streaming")
                resources.stop_event = display_event
                await subscriber.stop()
                stop_signal.set()

        subscriber = NCSubscriber.for_thread_display_events(
            nc=nc,
            topic_manager=topic_manager,
            handler=response_aggregator,
        )
        resources.subscriber = subscriber
        await subscriber.start()
        logger.debug(f"Subscriber created for subject: {subscriber.subject}")

        # Trigger the agent interaction via WebSocket
        await ws_receiver.receive_event(ws_event, user)

        return resources

    @staticmethod
    async def start_json_chat_interaction(
        user: AuthenticatedUser,
        agent_class: str,
        agent_id: str,
        messages: List[ChatMessage],
        nc: NATS,
        ws_receiver: WebSocketReceiver,
        thread_id: Optional[str] = None,
    ) -> JsonResources:
        """
        Starts a JSON-based chat interaction, waiting for all events before returning.
        """
        ws_event, topic_manager = ChatService._initialize_interaction(
            user=user,
            agent_class=agent_class,
            agent_id=agent_id,
            messages=messages,
            thread_id=thread_id,
            subscribe_to_thread=True
        )
        return await ChatService.start_json_event_interaction(user, ws_event, topic_manager, nc, ws_receiver)

    @staticmethod
    async def start_json_event_interaction(
        user: AuthenticatedUser,
        ws_event: WSUserEvent,
        topic_manager: AgentThreadTopicManager,
        nc: NATS,
        ws_receiver: WebSocketReceiver,
    ):
        stop_signal = asyncio.Event()
        chunk_events: List[ChunkEvent] = []
        costs = LLMCosts.from_zero()
        model_name = f"{topic_manager.agent_class}/{topic_manager.agent_id}"

        resources = JsonResources(
            stop_signal=stop_signal,
            subscriber=None,  # Will be set after subscriber creation.
            chunk_events=chunk_events,
            costs=costs,
            model_name=model_name,
            stop_event=None,
        )

        async def response_aggregator(display_event: DisplayEvent, topic: AgentTopic):
            logger.debug(f"Received display event: {display_event}")
            is_primary_agent = topic.agent_class == topic_manager.agent_class and topic.agent_id == topic_manager.agent_id
            if isinstance(display_event, ChunkEvent):
                resources.chunk_events.append(display_event)
            elif isinstance(display_event, HumanInTheLoopRequestEvent):
                resources.stop_event = display_event
                await subscriber.stop()
                stop_signal.set()
            elif isinstance(display_event, StopEvent) and is_primary_agent:
                logger.debug("Received stop event. Stop streaming")
                resources.stop_event = display_event
                await resources.subscriber.stop()
                resources.stop_signal.set()
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
        await ws_receiver.receive_event(ws_event, user)

        return resources

    @staticmethod
    def build_json_response_content(
        chunk_events: List[ChunkEvent], stop_event: Optional[StopEvent | HumanInTheLoopRequestEvent]
    ) -> str:
        """
        Construct a JSON response from collected chunk events.
        """
        sorted_chunks = sorted(chunk_events, key=lambda x: x.created_at)
        content = "".join(chunk.content for chunk in sorted_chunks)
        if isinstance(stop_event, HumanInTheLoopRequestEvent):
            content += stop_event.question
        return content
