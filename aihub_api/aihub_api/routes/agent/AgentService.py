import asyncio
import logging
from asyncio import sleep
from typing import Annotated, Any

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.infrastructure.api.DiscoverySettings import DiscoverySettings
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
from aihub_lib.nats.events.discovery.agent.AgentClassDiscoveryResponseEvent import AgentClassDiscoveryResponseEvent
from aihub_lib.nats.events.discovery.ClassDiscoveryRequestEvent import ClassDiscoveryRequestEvent
from aihub_lib.nats.events.human_in_the_loop.request import HumanInTheLoopRequestEvent
from aihub_lib.nats.publishers.NCPublisher import NCPublisher
from aihub_lib.nats.subscribers.agent.AgentNCSubscriber import AgentNCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentClassTopicManager import AgentClassTopicManager
from aihub_lib.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topics import AgentInstanceTopic
from aihub_lib.nats.topics.discovery.agent.AgentClassDiscoveryTopic import AgentClassDiscoveryTopic
from aihub_lib.persistence.agents.AgentConfigEntityDocument import AgentConfigEntityDocument
from aihub_lib.persistence.agents.AgentEntity import AgentEntity
from aihub_lib.persistence.messaging.entities.ThreadEntity import Agent, ThreadEntity, User
from aihub_lib.routes.chat.ChatService import ChatService, JsonResources, StreamingResources
from bson import ObjectId
from cachetools import TTLCache
from fastapi import HTTPException
from nats.aio.client import Client as NATS

from aihub_api.routes.agent.dto.AgentClassDTO import AgentClassDTO
from aihub_api.routes.agent.dto.AgentDTO import AgentDTO
from aihub_api.routes.agent.dto.AgentInstanceDTO import AgentInstanceDTO
from aihub_api.routes.agent.dto.CreateAgentRequest import CreateAgentRequest
from aihub_api.routes.agent.dto.MinimalAgentDTO import MinimalAgentDTO
from aihub_api.routes.thread.dto.ThreadDTO import ThreadDTO
from aihub_api.routes.thread.ThreadService import ThreadService

logger = logging.getLogger(__name__)

# In-memory caches to avoid repeatedly querying NATS for agent info
DISCOVER_AGENTS_CACHE = TTLCache(maxsize=100, ttl=60)  # Cache the entire agent list for 60s
GET_AGENT_INSTANCE_CACHE = TTLCache(maxsize=100, ttl=60)  # Cache individual agents for 60s
GET_AGENT_CLASS_CACHE = TTLCache(maxsize=100, ttl=60)  # Cache agent classes for 60s

# Discovery settings for configurable timeouts
discovery_settings = DiscoverySettings()


class AgentService:
    """
    Provides functionality to discover and retrieve agent information via NATS-based discovery events.
    `AgentService` acts as the business logic layer for agent operations,
    isolating NATS-based discovery requests from the HTTP layer.
    """

    @staticmethod
    @trace_fn
    def get_minimal_agent(agent_class: str, agent_id: str, t: LocaleHandler) -> MinimalAgentDTO:
        """Returns minimal details for an agent from database."""
        agent_entity = AgentEntity.get_agent(agent_class=agent_class, agent_id=agent_id)
        return MinimalAgentDTO.from_entity(agent_entity, t)

    @staticmethod
    @trace_fn
    async def get_agent(nc: NATS, agent_class: str, agent_id: str, t: LocaleHandler) -> AgentDTO:
        """
        Returns details for a given agent from the database.
        Online status is derived from the last_discovered timestamp.
        """
        agent = AgentEntity.get_agent(agent_class, agent_id)
        if agent is None:
            raise HTTPException(status_code=404, detail=f"Agent {agent_class}.{agent_id} not found.")
        return AgentDTO.from_entity(agent, t)

    @staticmethod
    @trace_fn
    async def get_agents(nc: NATS, t: LocaleHandler) -> list[AgentDTO]:
        """
        Returns all registered agents from the database.

        Online status is determined by the last_discovered timestamp - agents that responded
        to a discovery broadcast within AgentEntity.ONLINE_THRESHOLD are considered online.
        Discovery runs asynchronously via AgentEndpointsDiscoveryService every 60 seconds.
        """
        return [AgentDTO.from_entity(agent, t) for agent in AgentEntity.get_agents()]

    @staticmethod
    @trace_fn
    async def discover_agent_instance(nc: NATS, agent_class: str, agent_id: str) -> AgentInstanceDTO:
        """
        Retrieves details about a specific agent. If cached, returns immediately.
        Otherwise, sends a targeted discovery request and waits for a response.
        """
        cache_key = (agent_class, agent_id)

        if cache_key in GET_AGENT_INSTANCE_CACHE:
            return GET_AGENT_INSTANCE_CACHE[cache_key]

        agent_class_dto = await AgentService._discover_agent_class(nc, agent_class)

        configs = AgentConfigEntityDocument.find_for_class(agent_class)
        for config in configs:
            if config.agent_id == agent_id:
                agent_config = AgentConfig.from_entity(config)
                agent_instance_dto = AgentInstanceDTO.from_class_and_config(
                    class_dto=agent_class_dto,
                    agent_config=agent_config,
                )
                GET_AGENT_INSTANCE_CACHE[cache_key] = agent_instance_dto
                return agent_instance_dto

        if agent_class_dto.default_agent_config.agent_id == agent_id:
            agent_instance_dto = AgentInstanceDTO.from_class_and_config(
                class_dto=agent_class_dto,
                agent_config=agent_class_dto.default_agent_config,
            )
            GET_AGENT_INSTANCE_CACHE[cache_key] = agent_instance_dto
            return agent_instance_dto

        raise HTTPException(status_code=404, detail=f"Agent {agent_class}.{agent_id} not found.")

    @staticmethod
    @trace_fn
    async def discover_agent_instances_by_class(nc: NATS, agent_class: str) -> list[AgentInstanceDTO]:
        """
        Retrieves all instances of a specific agent class. If cached, returns immediately.
        Otherwise, sends a targeted discovery request and waits for responses.
        """
        cache_key = (agent_class, "*")

        if cache_key in GET_AGENT_INSTANCE_CACHE:
            return GET_AGENT_INSTANCE_CACHE[cache_key]

        agent_class_dto = await AgentService._discover_agent_class(nc, agent_class)

        configs = AgentConfigEntityDocument.find_for_class(agent_class)
        agent_instance_dtos = []
        for config in configs:
            agent_config = AgentConfig.from_entity(config)
            agent_instance_dto = AgentInstanceDTO.from_class_and_config(
                class_dto=agent_class_dto,
                agent_config=agent_config,
            )
            agent_instance_dtos.append(agent_instance_dto)

        db_agent_ids = {config.agent_id for config in configs}

        if agent_class_dto.default_agent_config.agent_id not in db_agent_ids:
            agent_instance_dto = AgentInstanceDTO.from_class_and_config(
                class_dto=agent_class_dto,
                agent_config=agent_class_dto.default_agent_config,
            )
            agent_instance_dtos.append(agent_instance_dto)

        if len(agent_instance_dtos) > 0:
            GET_AGENT_INSTANCE_CACHE[cache_key] = agent_instance_dtos
            return agent_instance_dtos

        raise HTTPException(status_code=404, detail=f"No instances found for agent class {agent_class}.")

    @staticmethod
    async def _discover_agent_class(nc: NATS, agent_class: str) -> AgentClassDTO:
        """
        Retrieves details about a specific agent. If cached, returns immediately.
        Otherwise, sends a targeted discovery request and waits for a response.
        """
        cache_key = agent_class

        if cache_key in GET_AGENT_CLASS_CACHE:
            return GET_AGENT_CLASS_CACHE[cache_key]

        call_id = str(ObjectId())
        agent_class_dto: AgentClassDTO | None = None
        agent_found_event = asyncio.Event()

        async def discovery_handler(event: AgentClassDiscoveryResponseEvent, topic: AgentClassDiscoveryTopic):
            nonlocal agent_class_dto
            # Found the agent, stop subscriber and signal event
            await nc_subscriber.stop()
            agent_class_dto = AgentClassDTO(
                agent_class=event.agent_class,
                agent_config_specs=event.agent_config_specs,
                is_conversational=event.is_conversational,
                start_events=event.start_events,
                stop_events=event.stop_events,
                hitl_request_events=event.hitl_request_events,
                hitl_response_events=event.hitl_response_events,
                network_graph=event.network_graph,
                is_online=True,
                default_agent_config=event.default_agent_config,
            )
            agent_found_event.set()

        topic_manager = AgentClassTopicManager(agent_class=agent_class)
        nc_publisher = NCPublisher(f"AgentService{agent_class}DiscoversRequest", nc)
        nc_subscriber = AgentNCSubscriber.for_agent_class_discovery_response_events(
            nc,
            topic_manager,
            discovery_handler,
            call_id=call_id,
            subscriber_name=f"AgentService{agent_class}DiscoveryResponse",
        )
        await nc_subscriber.start()

        # Send discovery request for the specific agent
        await nc_publisher.publish_event(
            event=ClassDiscoveryRequestEvent(),
            subject=topic_manager.get_agent_class_discovery_subject_request(call_id=call_id),
        )

        # Wait for response with configurable timeout
        try:
            await asyncio.wait_for(agent_found_event.wait(), timeout=discovery_settings.CLASS_DISCOVERY_TIMEOUT)
        except TimeoutError:
            await nc_subscriber.stop()
            raise HTTPException(status_code=404, detail=f"Agent {agent_class} not found.")

        if agent_class_dto is not None:
            GET_AGENT_CLASS_CACHE[cache_key] = agent_class_dto
            return agent_class_dto

        raise HTTPException(status_code=404, detail=f"Agent {agent_class} not found.")

    @staticmethod
    @trace_fn
    async def discover_agent_instances(nc: NATS) -> list[AgentInstanceDTO]:
        """
        Discovers all agents by broadcasting a discovery request and waiting for responses.
        Returns a cached result if available.
        """
        cache_key = "all_agent_instances"

        if cache_key in DISCOVER_AGENTS_CACHE:
            return DISCOVER_AGENTS_CACHE[cache_key]

        # Step 1: Discover which agent classes are online
        online_agents: list[AgentClassDTO] = await AgentService._discover_agent_classes(nc)

        # Step 2: Get all configured agent instances from database
        configured_agents = []
        for agent in online_agents:
            agent_class = agent.agent_class
            configs = AgentConfigEntityDocument.find_for_class(agent_class)
            for config in configs:
                config_instance = AgentConfig.from_entity(config)
                agent_instance_dto = AgentInstanceDTO.from_class_and_config(
                    class_dto=agent,
                    agent_config=config_instance,
                )
                agent_instance_dto.create_or_update_agent_entity()
                configured_agents.append(agent_instance_dto)

            # Step 3: Check if default agent config is present in database
            db_agent_ids = {configured_agent.agent_id for configured_agent in configured_agents}
            if agent.default_agent_config.agent_id not in db_agent_ids:
                agent_instance_dto = AgentInstanceDTO.from_class_and_config(
                    class_dto=agent,
                    agent_config=agent.default_agent_config,
                )
                agent_instance_dto.create_or_update_agent_entity()
                configured_agents.append(agent_instance_dto)

        if len(configured_agents) > 0:
            DISCOVER_AGENTS_CACHE[cache_key] = configured_agents

        return configured_agents

    @staticmethod
    async def _discover_agent_classes(nc: NATS) -> list[AgentClassDTO]:
        """
        Discovers all agents by broadcasting a discovery request and waiting for responses.
        Returns a cached result if available.
        """
        cache_key = "all_agent_classes"

        if cache_key in DISCOVER_AGENTS_CACHE:
            return DISCOVER_AGENTS_CACHE[cache_key]

        call_id = str(ObjectId())
        discovery_responses: list[AgentClassDiscoveryResponseEvent] = []

        async def discovery_handler(event: AgentClassDiscoveryResponseEvent, topic: AgentClassDiscoveryTopic):
            discovery_responses.append(event)

        topic_manager = AgentTopicManager()
        nc_publisher = NCPublisher("AgentServiceClassDiscoversRequest", nc)
        nc_subscriber = AgentNCSubscriber.for_agent_class_discovery_response_events(
            nc, topic_manager, discovery_handler, call_id=call_id, subscriber_name="AgentServiceClassDiscoveryResponse"
        )
        await nc_subscriber.start()

        # Broadcast the discovery request
        await nc_publisher.publish_event(
            event=ClassDiscoveryRequestEvent(),
            subject=topic_manager.get_agent_class_discovery_subject_request(call_id=call_id),
        )

        # Wait briefly for responses
        await sleep(1)
        await nc_subscriber.stop()

        unique_agents_dict: dict[str, AgentClassDTO] = {}

        for response in discovery_responses:
            unique_key = response.agent_class

            if unique_key not in unique_agents_dict:
                agent_class_dto = AgentClassDTO.from_discovery_event(response)
                unique_agents_dict[unique_key] = agent_class_dto

        agents = list(unique_agents_dict.values())

        if len(agents) > 0:
            DISCOVER_AGENTS_CACHE[cache_key] = agents

        return agents

    @staticmethod
    @trace_fn
    async def discover_agents(nc: NATS, t: LocaleHandler) -> list[AgentDTO]:
        discovered_agents = await AgentService.discover_agent_instances(nc)
        return [AgentDTO.from_instance(agent_instance, is_online=True, t=t) for agent_instance in discovered_agents]

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
                agents=[Agent(agent_class=agent_class, agent_id=agent_id)],
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
        agent_config: AgentConfig,
        expected_type: type[StartEvent] | type[HumanInTheLoopResponseEvent],
        subscribe_to_thread: Annotated[
            bool, "Receive all events in thread, not just the ones from the specified agents"
        ] = False,
    ) -> StopEvent | HumanInTheLoopRequestEvent | ExceptionEvent:
        """
        Sends an event (start or HITL response) to a specific agent and waits for a response.
        """
        event: StartEvent | HumanInTheLoopResponseEvent = expected_type.from_raw_data(
            raw_event_data=raw_event_data,
            user=user,
            start_event_name=input_event_name,
            start_event_parents=input_event_parents,
            agent_config=agent_config,
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
        agent_config: AgentConfig,
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
            agent_config=agent_config,
            t=t,
        )

        if thread_id:
            thread = ThreadEntity.get_thread_by_id(str(thread_id))
        else:
            thread = ThreadEntity.create_thread(
                "chat",
                users=[User(user_id=user.id)],
                agents=[Agent(agent_class=agent_class, agent_id=agent_id)],
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
        event_queue = asyncio.Queue()

        resources = StreamingResources(
            stop_signal=stop_signal,
            subscriber=None,
            chunk_queue=event_queue,
            stop_event=None,
        )

        async def event_handler(event: DisplayEvent, topic: AgentInstanceTopic):
            """Handles ALL events and puts them in the queue without conversion"""
            logger.debug(f"Received event for streaming: {event}")

            # Put ALL events in the queue as raw events
            await event_queue.put(event)

            # Check if this is a stop event from the primary agent
            is_primary_agent = topic.agent_class == agent_class and topic.agent_id == agent_id

            if event.is_stop_event and is_primary_agent:
                logger.debug("Received stop event. Stopping stream")
                resources.stop_event = event
                await subscriber.stop()
                stop_signal.set()
            elif event.is_exception_event:
                logger.warning(f"Received exception event: {event}")
                resources.stop_event = event
                await subscriber.stop()
                stop_signal.set()
            elif event.is_hitl_request_event:
                logger.debug(f"Received HITL request event: {event}")
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

        # Trigger the agent interaction
        await external_agent_event_distributor.distribute_event(external_event, user)

        return resources

    @staticmethod
    @trace_fn
    async def get_paginated_agent_threads(
        *,
        agent_class: str,
        agent_id: str,
        t: LocaleHandler,
        page: int = 1,
        page_size: int = 20,
        user_id: str | None = None,
    ) -> tuple[int, list[ThreadDTO]]:
        """
        Retrieves a paginated list of threads that a specific agent is part of.
        """
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

        Returns the nested dict structure directly. The frontend handles
        flattening/unflattening for FormKit compatibility.

        Falls back to default_agent_config if no custom configuration exists.

        Args:
            agent_class: The agent's class identifier
            agent_id: The agent's instance identifier

        Returns:
            Dictionary containing the agent's configuration values (nested structure)
        """
        # First, check for custom configuration in agent_configs collection
        config_entity = AgentConfigEntityDocument.find_for_class_and_id(agent_class, agent_id)

        if config_entity and config_entity.config_data:
            return config_entity.config_data

        # Fall back to default_agent_config from AgentEntity
        agent_entity = AgentEntity.get_agent(agent_class, agent_id)
        if agent_entity and agent_entity.default_agent_config:
            return agent_entity.default_agent_config.config_data

        # If no configuration exists at all, return empty dict
        return {}

    @staticmethod
    @trace_fn
    async def update_agent_configuration(
        agent_class: str, agent_id: str, configuration: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Update the configuration data for a specific agent.

        Expects nested dict structure from the frontend (frontend handles conversion
        from FormKit's dot-notation format).

        Args:
            agent_class: The agent's class identifier
            agent_id: The agent's instance identifier
            configuration: The new configuration values (nested structure)

        Returns:
            Dictionary containing the updated configuration values (nested structure)
        """
        agent_entity = AgentEntity.get_agent(agent_class, agent_id)
        if not agent_entity:
            raise HTTPException(
                status_code=404,
                detail=f"Agent {agent_class}/{agent_id} not found. Cannot update configuration.",
            )

        # Validate configuration keys against form schema
        if agent_entity.agent_config_specs and agent_entity.agent_config_specs.form:
            standard_fields = {"name", "description", "icon", "agent_class", "agent_id"}
            form_field_names = {
                elem.name for elem in agent_entity.agent_config_specs.form if hasattr(elem, "name") and elem.name
            }
            valid_fields = standard_fields | form_field_names

            invalid_fields = set(configuration.keys()) - valid_fields
            if invalid_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid configuration fields: {', '.join(sorted(invalid_fields))}. "
                    f"Valid fields are: {', '.join(sorted(valid_fields))}",
                )

        # Find existing configuration or create new one
        config_entity = AgentConfigEntityDocument.find_for_class_and_id(agent_class, agent_id)

        if config_entity:
            config_entity.config_data = configuration
            config_entity.save()
        else:
            if not agent_entity.agent_config_specs:
                raise HTTPException(
                    status_code=404,
                    detail=f"Agent {agent_class}/{agent_id} has no config specs. Cannot create configuration.",
                )
            config_entity = AgentConfigEntityDocument(
                agent_class=agent_class,
                agent_id=agent_id,
                name=agent_entity.agent_config_specs.name,
                description=agent_entity.agent_config_specs.description,
                icon=agent_entity.agent_config_specs.icon,
                config_data=configuration,
            )
            config_entity.save()

        # Clear cache to ensure updated config is immediately visible
        AgentService._clear_cache()

        return configuration

    @staticmethod
    def _clear_cache() -> None:
        """
        Clears the in-memory caches used for agent discovery. Useful for testing purposes to ensure fresh discovery
        requests.
        """
        DISCOVER_AGENTS_CACHE.clear()
        GET_AGENT_INSTANCE_CACHE.clear()
        GET_AGENT_CLASS_CACHE.clear()

    @staticmethod
    @trace_fn
    async def get_agent_classes(nc: NATS, t: LocaleHandler) -> list[AgentClassDTO]:
        """
        Returns all discovered agent classes (types) that are currently online.
        Each agent class includes its form schema for configuration.

        This is used for the "Create New Agent" feature to populate the agent class dropdown.
        """
        agent_classes = await AgentService._discover_agent_classes(nc)
        return agent_classes

    @staticmethod
    @trace_fn
    async def create_agent(
        nc: NATS,
        request: CreateAgentRequest,
        t: LocaleHandler,
    ) -> AgentDTO:
        """
        Creates a new agent instance from an existing agent class.

        Args:
            nc: NATS client connection
            request: CreateAgentRequest with agent_class, agent_id, and configuration
            t: LocaleHandler for translations

        Returns:
            AgentDTO for the newly created agent

        Raises:
            HTTPException 404: Agent class not found
            HTTPException 409: Agent with this agent_class/agent_id already exists
        """
        from aihub_lib.persistence.i18n.LocaleStringEntity import LocaleStringEntity

        # Step 1: Verify the agent class exists (must be online/discovered)
        try:
            agent_class_dto = await AgentService._discover_agent_class(nc, request.agent_class)
        except HTTPException:
            raise HTTPException(
                status_code=404,
                detail=f"Agent class '{request.agent_class}' not found. Make sure the agent is running.",
            )

        # Step 2: Check agent_id uniqueness within the agent class
        existing_config = AgentConfigEntityDocument.find_for_class_and_id(request.agent_class, request.agent_id)
        if existing_config:
            raise HTTPException(
                status_code=409,
                detail=f"Agent '{request.agent_class}/{request.agent_id}' already exists.",
            )

        # Also check if it matches the default agent config
        if agent_class_dto.default_agent_config.agent_id == request.agent_id:
            raise HTTPException(
                status_code=409,
                detail=f"Agent ID '{request.agent_id}' is reserved for the default configuration.",
            )

        # Step 2.5: Validate configuration keys against form schema
        standard_fields = {"name", "description", "icon", "agent_class", "agent_id"}
        form_field_names = {
            elem.name for elem in agent_class_dto.agent_config_specs.form if hasattr(elem, "name") and elem.name
        }
        valid_fields = standard_fields | form_field_names

        invalid_fields = set(request.configuration.keys()) - valid_fields
        if invalid_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid configuration fields: {', '.join(sorted(invalid_fields))}. "
                f"Valid fields are: {', '.join(sorted(valid_fields))}",
            )

        # Step 3: Extract name, description, icon from configuration or use defaults
        config = request.configuration
        name_data = config.get("name", {})
        description_data = config.get("description", {})
        icon = config.get("icon", agent_class_dto.agent_config_specs.icon or "meteor-icons:robot")

        # Create LocaleStringEntity for name and description
        name_entity = LocaleStringEntity(
            de=name_data.get("de", f"New {request.agent_class}"),
            en=name_data.get("en", f"New {request.agent_class}"),
            fr=name_data.get("fr", f"Nouveau {request.agent_class}"),
            it=name_data.get("it", f"Nuovo {request.agent_class}"),
        )
        description_entity = LocaleStringEntity(
            de=description_data.get("de", ""),
            en=description_data.get("en", ""),
            fr=description_data.get("fr", ""),
            it=description_data.get("it", ""),
        )

        # Step 4: Create AgentConfigEntityDocument with full configuration
        # Include agent_class and agent_id in the config_data
        full_config_data = {
            **config,
            "agent_class": request.agent_class,
            "agent_id": request.agent_id,
        }

        config_entity = AgentConfigEntityDocument(
            agent_class=request.agent_class,
            agent_id=request.agent_id,
            name=name_entity,
            description=description_entity,
            icon=icon,
            config_data=full_config_data,
        )
        config_entity.save()

        # Step 5: Create AgentEntity for the new instance
        # Wrap in try/except to rollback config on failure
        try:
            agent_config = AgentConfig.from_entity(config_entity)
            agent_instance_dto = AgentInstanceDTO.from_class_and_config(
                class_dto=agent_class_dto,
                agent_config=agent_config,
            )
            agent_instance_dto.create_or_update_agent_entity()
        except Exception:
            # Rollback: delete the config we just created
            config_entity.delete()
            raise

        # Step 6: Clear cache to ensure fresh data
        AgentService._clear_cache()

        # Step 7: Return the created agent
        agent_entity = AgentEntity.get_agent(request.agent_class, request.agent_id)
        if not agent_entity:
            raise HTTPException(
                status_code=500,
                detail="Failed to create agent. Please try again.",
            )

        return AgentDTO.from_entity(agent_entity, t)

    @staticmethod
    @trace_fn
    async def delete_agent(agent_class: str, agent_id: str) -> None:
        """
        Deletes an agent instance by removing its configuration from the database.

        Only user-created agents (stored in AgentConfigEntityDocument) can be deleted.
        Default agent configurations (from the agent class itself) cannot be deleted.

        Args:
            agent_class: The agent class identifier
            agent_id: The agent instance identifier

        Raises:
            HTTPException 403: Attempting to delete a default agent configuration
            HTTPException 404: Agent configuration not found
        """
        # Explicit check: prevent deletion of default agent configurations
        # Get any agent entity of this class to check its default_agent_config
        any_agent_of_class = AgentEntity.objects(agent_class=agent_class).first()
        if any_agent_of_class and any_agent_of_class.default_agent_config:
            default_id = any_agent_of_class.default_agent_config.agent_id
            if default_id == agent_id:
                raise HTTPException(
                    status_code=403,
                    detail=f"Cannot delete default agent configuration '{agent_class}/{agent_id}'. "
                    "Default configurations are managed by the agent class itself.",
                )

        # Only user-created agent configs can be deleted.
        # Default configs (from the agent class itself) are not stored in AgentConfigEntityDocument,
        # so find_for_class_and_id will return None for them, preventing deletion.
        config = AgentConfigEntityDocument.find_for_class_and_id(agent_class, agent_id)
        if not config:
            raise HTTPException(
                status_code=404,
                detail=f"Agent configuration '{agent_class}/{agent_id}' not found. "
                "Only user-created configurations can be deleted; default configurations cannot be removed.",
            )

        # Delete the configuration
        AgentConfigEntityDocument.delete_if_exists_for_class_and_id(agent_class, agent_id)

        # Also delete the agent entity if it exists
        agent_entity = AgentEntity.get_agent(agent_class, agent_id)
        if agent_entity:
            agent_entity.delete()

        # Clear cache to ensure fresh data
        AgentService._clear_cache()
