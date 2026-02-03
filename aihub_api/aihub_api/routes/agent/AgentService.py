import asyncio
import logging
from typing import Annotated, Any

from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.nats.distributor.events.ExternalAgentEvent import ExternalAgentEvent
from aihub_lib.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from aihub_lib.nats.events import (
    BaseEvent,
    DisplayEvent,
    ExceptionEvent,
    HumanInTheLoopResponseEvent,
    StartEvent,
    StopEvent,
)
from aihub_lib.nats.events.discovery.agent.AgentConfigSpecs import AgentConfigSpecs
from aihub_lib.nats.events.human_in_the_loop.request import HumanInTheLoopRequestEvent
from aihub_lib.nats.subscribers.agent.AgentNCSubscriber import AgentNCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from aihub_lib.nats.topics import AgentInstanceTopic
from aihub_lib.persistence.agents.AgentClassEntity import AgentClassEntity
from aihub_lib.persistence.agents.AgentConfigEntityDocument import AgentConfigEntityDocument
from aihub_lib.persistence.i18n.LocaleStringEntity import LocaleStringEntity
from aihub_lib.persistence.messaging.entities.ThreadEntity import AgentInstanceRef, ThreadEntity, User
from aihub_lib.routes.chat.ChatService import ChatService, JsonResources, StreamingResources
from bson import ObjectId
from fastapi import HTTPException
from nats.aio.client import Client as NATS
from pydantic import ValidationError

from aihub_api.routes.agent.dto.AgentClassDTO import AgentClassDTO
from aihub_api.routes.agent.dto.CreateAgentInstanceRequest import CreateAgentInstanceRequest
from aihub_api.routes.agent.dto.FullAgentInstanceDTO import FullAgentInstanceDTO
from aihub_api.routes.agent.dto.MinimalAgentInstanceDTO import MinimalAgentInstanceDTO
from aihub_api.routes.thread.dto.ThreadDTO import ThreadDTO
from aihub_api.routes.thread.ThreadService import ThreadService
from aihub_api.services.ModelCreationService import ModelCreationService

logger = logging.getLogger(__name__)


def _normalize_empty_objects_to_none(value: Any) -> Any:
    """
    Recursively convert empty dicts {} to None.
    Handles FormKit form submissions where disabled/unconfigured nested objects
    are sent as empty dicts but should be validated as None.
    """
    if value is None:
        return None

    if isinstance(value, dict):
        if not value:
            return None
        return {k: _normalize_empty_objects_to_none(v) for k, v in value.items()}

    if isinstance(value, list):
        return [_normalize_empty_objects_to_none(item) for item in value]

    return value


def _normalize_empty_locale_strings(value: Any) -> Any:
    """Recursively normalize empty LocaleString data from FormKit to None."""
    if value is None:
        return None

    if isinstance(value, dict):
        locale_keys = {"de", "en", "fr", "it"}
        if set(value.keys()).issubset(locale_keys):
            if not value or all(not val for val in value.values()):
                return None

        return {k: _normalize_empty_locale_strings(v) for k, v in value.items()}

    if isinstance(value, list):
        return [_normalize_empty_locale_strings(item) for item in value]

    return value


class AgentService:
    """
    Provides functionality to retrieve and manage agent information from the database.
    Online status is determined by the AgentEndpointsDiscoveryService which periodically
    broadcasts NATS discovery requests and updates `last_discovered` timestamps.
    """

    @staticmethod
    @trace_fn
    def get_minimal_agent_instance(agent_class: str, agent_id: str, t: LocaleHandler) -> MinimalAgentInstanceDTO:
        """Returns minimal details for an agent instance from database."""
        class_entity = AgentClassEntity.get_by_agent_class(agent_class=agent_class)
        if class_entity is None:
            raise HTTPException(status_code=404, detail=f"Agent class {agent_class} not found.")

        config_entity = AgentConfigEntityDocument.find_for_class_and_id(agent_class, agent_id)
        if config_entity is None:
            raise HTTPException(status_code=404, detail=f"Agent config {agent_class}/{agent_id} not found.")

        return MinimalAgentInstanceDTO.from_class_and_config(class_entity, config_entity, t)

    @staticmethod
    @trace_fn
    async def get_agent_instance(agent_class: str, agent_id: str, t: LocaleHandler) -> FullAgentInstanceDTO:
        """
        Returns details for a given agent instance from the database.
        Online status is derived from the last_discovered timestamp on the class entity.
        """
        class_entity = AgentClassEntity.get_by_agent_class(agent_class)
        if class_entity is None:
            raise HTTPException(status_code=404, detail=f"Agent class {agent_class} not found.")

        config_entity = AgentConfigEntityDocument.find_for_class_and_id(agent_class, agent_id)
        if config_entity is None:
            raise HTTPException(status_code=404, detail=f"Agent instance {agent_class}/{agent_id} not found.")

        return FullAgentInstanceDTO.from_class_and_config(class_entity, config_entity, t)

    @staticmethod
    @trace_fn
    async def get_all_agent_instances(t: LocaleHandler, online: bool | None = None) -> list[FullAgentInstanceDTO]:
        """
        Returns all registered agent instances from the database.
        Online status is determined by the last_discovered timestamp - agents that responded
        to a discovery broadcast within AgentClassEntity.ONLINE_THRESHOLD are considered online.
        """
        agents = []
        for class_entity in AgentClassEntity.get_all():
            if online is not None and class_entity.is_online != online:
                continue

            configs = AgentConfigEntityDocument.find_for_class(class_entity.agent_class)
            for config_entity in configs:
                agents.append(FullAgentInstanceDTO.from_class_and_config(class_entity, config_entity, t))
        return agents

    @staticmethod
    async def _send_event(
        *,
        nc: NATS,
        external_agent_event_distributor: ExternalAgentEventDistributor,
        user: UserIdentity,
        input_event: BaseEvent,
        agent_class: str,
        agent_id: str,
        thread_id: ObjectId | None = None,
        display_id: ObjectId | None = None,
        subscribe_to_thread: Annotated[
            bool, "Receive all events in thread, not just the ones from the specified agents"
        ] = False,
    ) -> StopEvent | HumanInTheLoopRequestEvent | ExceptionEvent:
        """Sends an event to a specific agent."""
        if thread_id:
            thread = ThreadEntity.get_thread_by_id(str(thread_id))
        else:
            thread = ThreadEntity.create_thread(
                "chat",
                users=[User(user_id=user.id)],
                agents=[AgentInstanceRef(agent_class=agent_class, agent_id=agent_id)],
            )

        topic_manager = AgentThreadTopicManager(
            agent_class="*" if subscribe_to_thread else agent_class,
            agent_id="*" if subscribe_to_thread else agent_id,
            thread_id=str(thread.id),
            display_id=display_id or str(ObjectId()),
            run_id="*",
        )
        external_event = ExternalAgentEvent(
            thread_id=topic_manager.thread_id,
            display_id=topic_manager.display_id,
            event=input_event,
        )
        resources: JsonResources = await ChatService.start_json_event_interaction(
            user=user,
            agent_class=agent_class,
            agent_id=agent_id,
            external_event=external_event,
            topic_manager=topic_manager,
            nc=nc,
            external_agent_event_distributor=external_agent_event_distributor,
        )

        await resources.stop_signal.wait()
        await resources.subscriber.stop()

        return resources.stop_event

    @staticmethod
    @trace_fn
    async def send_agent_input_event(
        *,
        nc: NATS,
        agent_class: str,
        agent_id: str,
        input_event_parents: list[str],
        input_event_name: str,
        raw_event_data: dict,
        external_agent_event_distributor: ExternalAgentEventDistributor,
        thread_id: ObjectId | None,
        display_id: ObjectId | None,
        user: UserIdentity,
        t: LocaleHandler,
        expected_type: type[StartEvent] | type[HumanInTheLoopResponseEvent],
        subscribe_to_thread: Annotated[
            bool, "Receive all events in thread, not just the ones from the specified agents"
        ] = False,
    ) -> StopEvent | HumanInTheLoopRequestEvent | ExceptionEvent:
        """Sends an event (start or HITL response) to a specific agent and waits for a response."""
        event: StartEvent | HumanInTheLoopResponseEvent = expected_type.from_raw_data(
            raw_event_data=raw_event_data,
            user=user,
            start_event_name=input_event_name,
            start_event_parents=input_event_parents,
            t=t,
        )

        return await AgentService._send_event(
            nc=nc,
            external_agent_event_distributor=external_agent_event_distributor,
            user=user,
            input_event=event,
            agent_class=agent_class,
            agent_id=agent_id,
            thread_id=thread_id,
            display_id=display_id,
            subscribe_to_thread=subscribe_to_thread,
        )

    @staticmethod
    @trace_fn
    async def send_agent_input_event_stream(
        *,
        nc: NATS,
        agent_class: str,
        agent_id: str,
        input_event_parents: list[str],
        input_event_name: str,
        raw_event_data: dict,
        external_agent_event_distributor: ExternalAgentEventDistributor,
        thread_id: ObjectId | None,
        display_id: ObjectId | None,
        user: UserIdentity,
        t: LocaleHandler,
        expected_type: type[StartEvent] | type[HumanInTheLoopResponseEvent],
        subscribe_to_thread: Annotated[
            bool, "Receive all events in thread, not just the ones from the specified agents"
        ] = False,
    ) -> StreamingResources:
        """
        Sends an event (start or HITL response) to a specific agent and returns streaming resources for SSE.
        Yields ALL events (not just chunks) as raw events without conversion.
        """
        event: StartEvent | HumanInTheLoopResponseEvent = expected_type.from_raw_data(
            raw_event_data=raw_event_data,
            user=user,
            start_event_name=input_event_name,
            start_event_parents=input_event_parents,
            t=t,
        )

        if thread_id:
            thread = ThreadEntity.get_thread_by_id(str(thread_id))
        else:
            thread = ThreadEntity.create_thread(
                "chat",
                users=[User(user_id=user.id)],
                agents=[AgentInstanceRef(agent_class=agent_class, agent_id=agent_id)],
            )

        topic_manager = AgentThreadTopicManager(
            agent_class="*" if subscribe_to_thread else agent_class,
            agent_id="*" if subscribe_to_thread else agent_id,
            thread_id=str(thread.id),
            display_id=display_id or str(ObjectId()),
            run_id="*",
        )

        external_event = ExternalAgentEvent(
            thread_id=topic_manager.thread_id,
            display_id=topic_manager.display_id,
            event=event,
        )

        stop_signal = asyncio.Event()
        event_queue: asyncio.Queue[DisplayEvent] = asyncio.Queue()

        resources = StreamingResources(
            stop_signal=stop_signal,
            subscriber=None,
            chunk_queue=event_queue,
            stop_event=None,
        )

        async def event_handler(event: DisplayEvent, topic: AgentInstanceTopic):
            """Handles ALL events and puts them in the queue without conversion."""
            logger.debug(f"Received event for streaming: {event.event_name}")

            await event_queue.put(event)

            is_primary_agent = topic.agent_class == agent_class and topic.agent_id == agent_id

            if event.is_stop_event and is_primary_agent:
                logger.debug("Received stop event. Stopping stream")
                resources.stop_event = event
                await subscriber.stop()
                stop_signal.set()
            elif event.is_exception_event:
                logger.warning(f"Received exception event: {event.event_name}")
                resources.stop_event = event
                await subscriber.stop()
                stop_signal.set()
            elif event.is_hitl_request_event:
                logger.debug(f"Received HITL request event: {event.event_name}")
                resources.stop_event = event
                await subscriber.stop()
                stop_signal.set()

        subscriber = AgentNCSubscriber.for_thread_display_events(
            nc=nc,
            topic_manager=topic_manager,
            handler=event_handler,
            subscriber_name="AgentServiceSendAgentInputEventStream",
        )
        resources.subscriber = subscriber
        await subscriber.start()
        logger.debug(f"Subscriber created for streaming subject: {subscriber.subject}")

        await external_agent_event_distributor.distribute_event(external_event, user)

        return resources

    @staticmethod
    @trace_fn
    async def get_agent_instance_threads(
        *,
        agent_class: str,
        agent_id: str,
        t: LocaleHandler,
        page: int = 1,
        page_size: int = 20,
        user_id: str | None = None,
    ) -> tuple[int, list[ThreadDTO]]:
        """Retrieves a paginated list of threads that a specific agent instance is part of."""
        return await ThreadService.get_paginated_threads_for_agent(
            agent_class,
            agent_id,
            t=t,
            page=page,
            page_size=page_size,
            user_id=user_id,
        )

    @staticmethod
    @trace_fn
    async def get_agent_configuration(agent_class: str, agent_id: str) -> dict[str, Any]:
        """
        Retrieve the current configuration data for a specific agent.
        Returns empty dict if no configuration has been saved.
        """
        config_entity = AgentConfigEntityDocument.find_for_class_and_id(agent_class, agent_id)
        if config_entity and config_entity.config_data:
            return config_entity.config_data
        return {}

    @staticmethod
    @trace_fn
    async def update_agent_instance(agent_class: str, agent_id: str, configuration: dict[str, Any]) -> dict[str, Any]:
        """
        Update the configuration data for a specific agent instance.
        Validates the configuration against the agent's schema before saving.
        """
        class_entity = AgentClassEntity.get_by_agent_class(agent_class)
        if not class_entity:
            raise HTTPException(status_code=404, detail=f"Agent class {agent_class} not found.")

        config_entity = AgentConfigEntityDocument.find_for_class_and_id(agent_class, agent_id)
        if not config_entity:
            raise HTTPException(status_code=404, detail=f"Agent config {agent_class}/{agent_id} not found.")

        # Filter out FormKit internal fields (those starting with '_')
        configuration = {k: v for k, v in configuration.items() if not k.startswith("_")}

        # Normalize configuration before validation
        configuration = _normalize_empty_objects_to_none(configuration)
        configuration = _normalize_empty_locale_strings(configuration)

        config_model = ModelCreationService.create_agent_config_model(
            AgentConfigSpecs(
                agent_class=class_entity.agent_config_specs.agent_class,
                agent_config_schema=class_entity.agent_config_specs.agent_config_schema,
            )
        )
        try:
            config_instance = config_model.model_validate(configuration)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Configuration validation failed: {e.errors()}")

        if hasattr(config_instance, "name") and config_instance.name:
            config_entity.name = LocaleStringEntity.from_locale_string(config_instance.name)

        if hasattr(config_instance, "description") and config_instance.description:
            config_entity.description = LocaleStringEntity.from_locale_string(config_instance.description)

        if hasattr(config_instance, "icon") and config_instance.icon:
            config_entity.icon = config_instance.icon

        config_entity.config_data = configuration
        config_entity.save()

        return configuration

    @staticmethod
    @trace_fn
    async def get_agent_classes(t: LocaleHandler, online: bool | None = None) -> list[AgentClassDTO]:
        """Returns all agent classes from the database."""
        agent_classes = []
        for class_entity in AgentClassEntity.get_all():
            if online is not None and class_entity.is_online != online:
                continue
            agent_classes.append(AgentClassDTO.from_entity(class_entity, t))
        return agent_classes

    @staticmethod
    @trace_fn
    async def get_agent_class(agent_class: str, t: LocaleHandler) -> AgentClassDTO:
        """Returns a specific agent class from the database."""
        class_entity = AgentClassEntity.get_by_agent_class(agent_class)
        if class_entity is None:
            raise HTTPException(status_code=404, detail=f"Agent class {agent_class} not found.")
        return AgentClassDTO.from_entity(class_entity, t)

    @staticmethod
    @trace_fn
    async def get_agent_class_instances(agent_class: str, t: LocaleHandler) -> list[FullAgentInstanceDTO]:
        """Returns all instances of a specific agent class from the database."""
        class_entity = AgentClassEntity.get_by_agent_class(agent_class)
        if class_entity is None:
            raise HTTPException(status_code=404, detail=f"Agent class {agent_class} not found.")

        instances = []
        configs = AgentConfigEntityDocument.find_for_class(agent_class)
        for config_entity in configs:
            instances.append(FullAgentInstanceDTO.from_class_and_config(class_entity, config_entity, t))
        return instances

    @staticmethod
    @trace_fn
    async def create_agent_instance(
        agent_class: str,
        request: CreateAgentInstanceRequest,
        t: LocaleHandler,
    ) -> FullAgentInstanceDTO:
        """
        Creates a new agent instance from an existing agent class.
        Requires the agent class to be online (i.e., the agent must be running).
        """
        class_entity = AgentClassEntity.get_by_agent_class(agent_class)
        if class_entity is None:
            raise HTTPException(status_code=404, detail=f"Agent class '{agent_class}' not found.")

        if not class_entity.is_online:
            raise HTTPException(
                status_code=503,
                detail=f"Agent class '{agent_class}' is not online. Make sure the agent is running.",
            )

        existing_config = AgentConfigEntityDocument.find_for_class_and_id(agent_class, request.agent_id)
        if existing_config:
            raise HTTPException(
                status_code=409, detail=f"Agent instance '{agent_class}/{request.agent_id}' already exists."
            )

        # Normalize configuration before validation
        config = _normalize_empty_objects_to_none(request.configuration)
        config = _normalize_empty_locale_strings(config) or {}

        config_model = ModelCreationService.create_agent_config_model(
            AgentConfigSpecs(
                agent_class=class_entity.agent_config_specs.agent_class,
                agent_config_schema=class_entity.agent_config_specs.agent_config_schema,
            )
        )
        try:
            config_instance = config_model.model_validate(config)
        except ValidationError as e:
            error_messages = []
            for error in e.errors():
                field_path = ".".join(str(loc) for loc in error["loc"])
                error_messages.append(f"{field_path}: {error['msg']}")
            raise HTTPException(status_code=400, detail=f"Configuration validation failed: {'; '.join(error_messages)}")

        name = config_instance.name if hasattr(config_instance, "name") and config_instance.name else None
        description = (
            config_instance.description
            if hasattr(config_instance, "description") and config_instance.description
            else None
        )
        icon = (
            config_instance.icon
            if hasattr(config_instance, "icon") and config_instance.icon
            else class_entity.icon or "mage:robot"
        )

        name_entity = (
            LocaleStringEntity.from_locale_string(name)
            if name
            else LocaleStringEntity(
                de=f"New {agent_class}",
                en=f"New {agent_class}",
                fr=f"Nouveau {agent_class}",
                it=f"Nuovo {agent_class}",
            )
        )
        description_entity = (
            LocaleStringEntity.from_locale_string(description)
            if description
            else LocaleStringEntity(de="", en="", fr="", it="")
        )

        full_config_data = {
            **config,
            "agent_class": agent_class,
            "agent_id": request.agent_id,
        }

        config_entity = AgentConfigEntityDocument(
            agent_class=agent_class,
            agent_id=request.agent_id,
            name=name_entity,
            description=description_entity,
            icon=icon,
            config_data=full_config_data,
        )
        config_entity.save()

        return FullAgentInstanceDTO.from_class_and_config(class_entity, config_entity, t)

    @staticmethod
    @trace_fn
    async def delete_agent_instance(agent_class: str, agent_id: str) -> None:
        """Deletes an agent instance by removing its configuration from the database."""
        config = AgentConfigEntityDocument.find_for_class_and_id(agent_class, agent_id)
        if not config:
            raise HTTPException(status_code=404, detail=f"Agent instance '{agent_class}/{agent_id}' not found.")

        AgentConfigEntityDocument.delete_if_exists_for_class_and_id(agent_class, agent_id)
