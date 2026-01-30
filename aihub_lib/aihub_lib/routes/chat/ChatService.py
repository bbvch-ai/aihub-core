import asyncio
import logging
from dataclasses import dataclass
from typing import Annotated

import mongoengine.errors
from bson import ObjectId
from fastapi import HTTPException
from llama_index.core.base.llms.types import ChatMessage
from nats.aio.client import Client as NATS
from redis.asyncio import Redis

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.auth.usage.period_labels import build_exceeded_detail
from aihub_lib.auth.usage.UsageLimitService import ResourceType, UsageLimitService
from aihub_lib.generative_ai.resources.costs.LLMCosts import LLMCosts
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.nats.distributor.events.ExternalAgentEvent import ExternalAgentEvent
from aihub_lib.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from aihub_lib.nats.events import (
    BaseEvent,
    ChunkEvent,
    DisplayEvent,
    ExceptionEvent,
    HumanInTheLoopRequestEvent,
    HumanInTheLoopResponseEvent,
    StopEvent,
    ThoughtEvent,
)
from aihub_lib.nats.events.user import UserMessageEvent
from aihub_lib.nats.events.user.UserUploadedFile import UserUploadedFile
from aihub_lib.nats.events.utils import get_parent_classes_until_base
from aihub_lib.nats.subscribers.agent.AgentNCSubscriber import AgentNCSubscriber
from aihub_lib.nats.subscribers.NCSubscriber import NCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from aihub_lib.nats.topics.agents.AgentInstanceTopic import AgentInstanceTopic
from aihub_lib.persistence.agents.AgentConfigEntityDocument import AgentConfigEntityDocument
from aihub_lib.persistence.messaging.entities.PersistedAgentEventEntity import PersistedAgentEventEntity
from aihub_lib.persistence.messaging.entities.ThreadEntity import Agent, ThreadEntity, User

logger = logging.getLogger(__name__)


@dataclass
class StreamingResources:
    stop_signal: asyncio.Event
    subscriber: NCSubscriber
    chunk_queue: asyncio.Queue
    stop_event: StopEvent | HumanInTheLoopRequestEvent | ExceptionEvent | None = (
        None  # Added field to store the final StopEvent
    )


@dataclass
class JsonResources:
    stop_signal: asyncio.Event
    subscriber: NCSubscriber
    chunk_events: list[ChunkEvent | ThoughtEvent]
    costs: LLMCosts
    model_name: str
    stop_event: StopEvent | HumanInTheLoopRequestEvent | ExceptionEvent | None = (
        None  # Added field to store the final StopEvent
    )


@dataclass
class ChatContent:
    content: str
    reasoning_content: str


class ChatService:
    """
    Orchestrates chat interactions for both streaming and JSON-based endpoints.
    """

    @staticmethod
    async def _check_usage_limit(
        redis: Redis | None,
        user: UserIdentity,
        agent_class: str,
        agent_id: str,
        locale: str | None = None,
    ) -> None:
        """Check usage limits and raise 429 if exceeded. No-op when redis is None."""
        if redis is None:
            return
        resource_path = UsageLimitService.build_resource_path(ResourceType.AGENT, agent_class, agent_id)
        usage_status = await UsageLimitService.check_and_increment(
            redis, user.id, user.roles, resource_path=resource_path
        )
        if usage_status.is_exceeded:
            raise HTTPException(
                status_code=429,
                detail=build_exceeded_detail(usage_status, locale=locale or "en"),
            )

    @staticmethod
    def _initialize_interaction(
        user: UserIdentity,
        agent_class: str,
        agent_id: str,
        messages: list[ChatMessage],
        thread_id: ObjectId | None = None,
        display_id: ObjectId | None = None,
        files: list[UserUploadedFile] | None = None,
        subscribe_to_thread: Annotated[
            bool, "Receive all events in thread, not just the ones from the specified agents"
        ] = False,
        locale: str | None = None,
    ) -> tuple[ExternalAgentEvent, AgentThreadTopicManager]:
        """
        Common initialization steps for both streaming and JSON interactions.
        """
        thread = None
        if thread_id:
            try:
                thread = ThreadEntity.get_thread_by_id(str(thread_id))
                if not thread:
                    raise mongoengine.errors.DoesNotExist()
                if user.id not in [u.user_id for u in thread.users]:
                    raise HTTPException(status_code=403, detail="User not part of the thread")
            except mongoengine.errors.DoesNotExist:
                pass

        if not thread:
            thread = ThreadEntity.create_thread(
                "chat",
                users=[User(user_id=user.id)],
                agents=[Agent(agent_class=agent_class, agent_id=agent_id)],
                thread_id=ObjectId(thread_id) or ObjectId(),
            )
        logger.debug(f"Created thread: {thread.id}")

        hitl_requests = PersistedAgentEventEntity.human_in_the_loop_request_events_for_thread(str(thread.id))
        logger.debug(f"hitl_requests: {hitl_requests}")

        hitl_responses = PersistedAgentEventEntity.human_in_the_loop_response_events_for_thread(str(thread.id))
        logger.debug(f"hitl_responses: {hitl_responses}")

        thread_id = str(thread.id)
        display_id = display_id or str(ObjectId())

        if len(hitl_requests) != len(hitl_responses):
            open_hitl_request = HumanInTheLoopRequestEvent.deserialize_event(hitl_requests[-1].event_data)
            topic = open_hitl_request.topic
            parent_classes = [topic.event_name, HumanInTheLoopResponseEvent.event_name_from_class()] + list(
                get_parent_classes_until_base(HumanInTheLoopResponseEvent, BaseEvent)
            )
            event = HumanInTheLoopResponseEvent.deserialize_event(
                {
                    "_event_name": topic.event_name,
                    "_parent_event_names": parent_classes,
                    "response": messages[-1].content,
                    "request_event": open_hitl_request.model_dump(),
                }
            )
            display_id = event.request_event.topic.display_id
        else:
            agent_config_entity = AgentConfigEntityDocument.find_for_class_and_id(agent_class, agent_id)
            if agent_config_entity is None:
                logger.info(f"Agent config not found for class {agent_class} and id {agent_id}. Using default config.")
                agent_config_dict = None
            else:
                agent_config_dict = AgentConfig.from_entity(agent_config_entity).model_dump()
            event = UserMessageEvent(
                messages=messages,
                user=user,
                locale=locale or LocaleHandler.DEFAULT_LOCALE,
                files=files,
                agent_config=agent_config_dict,
            )

        event = ExternalAgentEvent(
            thread_id=str(thread_id),
            display_id=str(display_id),
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
    @trace_fn
    async def start_stream_chat_interaction(
        user: UserIdentity,
        agent_class: str,
        agent_id: str,
        messages: list[ChatMessage],
        nc: NATS,
        external_agent_event_distributor: ExternalAgentEventDistributor,
        thread_id: ObjectId | None = None,
        display_id: ObjectId | None = None,
        files: list[UserUploadedFile] | None = None,
        locale: str | None = None,
        redis: Redis | None = None,
    ) -> StreamingResources:
        """
        Starts a streaming chat interaction and returns the resources for SSE streaming.
        """
        await ChatService._check_usage_limit(redis, user, agent_class, agent_id, locale)
        external_event, topic_manager = ChatService._initialize_interaction(
            user=user,
            agent_class=agent_class,
            agent_id=agent_id,
            messages=messages,
            thread_id=thread_id,
            display_id=display_id,
            files=files,
            subscribe_to_thread=True,
            locale=locale,
        )

        stop_signal = asyncio.Event()
        chunk_queue = asyncio.Queue()
        resources = StreamingResources(
            stop_signal=stop_signal,
            subscriber=None,  # Will be set after subscriber creation
            chunk_queue=chunk_queue,
            stop_event=None,
        )

        async def response_aggregator(event: DisplayEvent, topic: AgentInstanceTopic):
            is_primary_agent = topic.agent_class == agent_class and topic.agent_id == agent_id
            logger.debug(f"Received display event: {event}")
            if event.is_chunk_event:
                logger.debug(f"Received chunk event: {event}")
                await chunk_queue.put(event)
            elif event.is_hitl_request_event:
                logger.debug(f"Received HITL event: {event}")
                resources.stop_event = event
                await subscriber.stop()
                stop_signal.set()
            elif event.is_stop_event and is_primary_agent:
                logger.debug("Received stop event. Stop streaming")
                resources.stop_event = event
                await subscriber.stop()
                stop_signal.set()
            elif event.is_exception_event:
                logger.warning(f"Received exception event: {event}")
                resources.stop_event = event
                await subscriber.stop()
                stop_signal.set()

        subscriber = AgentNCSubscriber.for_thread_display_events(
            nc=nc,
            topic_manager=topic_manager,
            handler=response_aggregator,
            subscriber_name="ChatServiceStreamInteraction",
        )
        resources.subscriber = subscriber
        await subscriber.start()
        logger.debug(f"Subscriber created for subject: {subscriber.subject}")

        # Trigger the agent interaction via WebSocket
        await external_agent_event_distributor.distribute_event(external_event, user)

        return resources

    @staticmethod
    @trace_fn
    async def start_json_chat_interaction(
        user: UserIdentity,
        agent_class: str,
        agent_id: str,
        messages: list[ChatMessage],
        nc: NATS,
        external_agent_event_distributor: ExternalAgentEventDistributor,
        thread_id: ObjectId | None = None,
        display_id: ObjectId | None = None,
        files: list[UserUploadedFile] | None = None,
        locale: str | None = None,
        redis: Redis | None = None,
    ) -> JsonResources:
        """
        Starts a JSON-based chat interaction, waiting for all events before returning.
        """
        await ChatService._check_usage_limit(redis, user, agent_class, agent_id, locale)
        external_event, topic_manager = ChatService._initialize_interaction(
            user=user,
            agent_class=agent_class,
            agent_id=agent_id,
            messages=messages,
            thread_id=thread_id,
            display_id=display_id,
            files=files,
            subscribe_to_thread=True,
            locale=locale,
        )
        return await ChatService.start_json_event_interaction(
            user, agent_class, agent_id, external_event, topic_manager, nc, external_agent_event_distributor
        )

    @staticmethod
    @trace_fn
    async def start_json_event_interaction(
        user: UserIdentity,
        agent_class: str,
        agent_id: str,
        external_event: ExternalAgentEvent,
        topic_manager: AgentThreadTopicManager,
        nc: NATS,
        external_agent_event_distributor: ExternalAgentEventDistributor,
    ):
        stop_signal = asyncio.Event()
        chunk_events: list[ChunkEvent | ThoughtEvent] = []
        costs = LLMCosts.from_zero()
        model_name = f"{agent_class}/{agent_id}"

        resources = JsonResources(
            stop_signal=stop_signal,
            subscriber=None,  # Will be set after subscriber creation.
            chunk_events=chunk_events,
            costs=costs,
            model_name=model_name,
            stop_event=None,
        )

        async def response_aggregator(event: DisplayEvent, topic: AgentInstanceTopic):
            logger.debug(f"Received display event: {event}")
            is_primary_agent = topic.agent_class == agent_class and topic.agent_id == agent_id
            if event.is_chunk_event:
                resources.chunk_events.append(event)
            elif event.is_hitl_request_event:
                resources.stop_event = event
                await subscriber.stop()
                stop_signal.set()
            elif event.is_stop_event and is_primary_agent:
                logger.debug("Received stop event. Stop streaming")
                resources.stop_event = event
                await resources.subscriber.stop()
                resources.stop_signal.set()
            elif event.is_llm_cost_event:
                resources.costs += event
                resources.model_name = event.llm_name
            elif event.is_exception_event:
                logger.warning(f"Received exception event: {event}")
                resources.stop_event = event
                await resources.subscriber.stop()
                resources.stop_signal.set()

        subscriber = AgentNCSubscriber.for_thread_display_events(
            nc=nc,
            topic_manager=topic_manager,
            handler=response_aggregator,
            subscriber_name="ChatServiceJsonInteraction",
        )
        resources.subscriber = subscriber

        await subscriber.start()
        logger.debug(f"Subscriber created for subject: {subscriber.subject}")

        # Trigger the agent interaction
        await external_agent_event_distributor.distribute_event(external_event, user)

        return resources

    @staticmethod
    @trace_fn
    def build_json_response_content(
        chunk_events: list[ChunkEvent | ThoughtEvent], stop_event: StopEvent | HumanInTheLoopRequestEvent | None
    ) -> ChatContent:
        """
        Construct a JSON response from collected chunk events.
        """
        sorted_chunks = sorted(chunk_events, key=lambda x: x.created_at)
        chat_content = ChatContent(content="", reasoning_content="")
        chat_content.content = "".join(chunk.content for chunk in sorted_chunks)
        chat_content.reasoning_content = "".join(getattr(chunk, "reasoning_content", "") for chunk in sorted_chunks)
        if stop_event.is_hitl_request_event:
            chat_content.content += stop_event.question
        return chat_content
