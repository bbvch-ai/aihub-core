import asyncio
import time
from asyncio import sleep
from typing import Any

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.agents.visualizers.types.WorkflowGraph import WorkflowGraph
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.distributor.events.ExternalAgentEvent import ExternalAgentEvent
from aihub_lib.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from aihub_lib.nats.events import BaseEvent, ExceptionEvent, StartEvent, StopEvent
from aihub_lib.nats.events.discovery.agent.AgentClassDiscoveryResponseEvent import AgentClassDiscoveryResponseEvent
from aihub_lib.nats.events.discovery.ClassDiscoveryRequestEvent import ClassDiscoveryRequestEvent
from aihub_lib.nats.publishers.NCPublisher import NCPublisher
from aihub_lib.nats.subscribers.agent.AgentNCSubscriber import AgentNCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentClassTopicManager import AgentClassTopicManager
from aihub_lib.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topics.discovery.agent.AgentClassDiscoveryTopic import AgentClassDiscoveryTopic
from aihub_lib.persistence.agents.AgentConfigEntityDocument import AgentConfigEntityDocument
from aihub_lib.persistence.agents.AgentEntity import AgentEntity
from aihub_lib.persistence.messaging.entities.ThreadEntity import Agent, ThreadEntity, User
from aihub_lib.routes.chat.ChatService import ChatService, JsonResources
from bson import ObjectId
from cachetools import TTLCache
from fastapi import HTTPException
from nats.aio.client import Client as NATS

from aihub_api.routes.agent.dto.AgentClassDTO import AgentClassDTO
from aihub_api.routes.agent.dto.AgentDTO import AgentDTO
from aihub_api.routes.agent.dto.AgentInstanceDTO import AgentInstanceDTO
from aihub_api.routes.agent.dto.MinimalAgentDTO import MinimalAgentDTO
from aihub_api.routes.thread.dto.ThreadDTO import ThreadDTO
from aihub_api.routes.thread.ThreadService import ThreadService

# In-memory caches to avoid repeatedly querying NATS for agent info
DISCOVER_AGENTS_CACHE = TTLCache(maxsize=100, ttl=60)  # Cache the entire agent list for 60s
GET_AGENT_INSTANCE_CACHE = TTLCache(maxsize=100, ttl=60)  # Cache individual agents for 60s
GET_AGENT_CLASS_CACHE = TTLCache(maxsize=100, ttl=60)  # Cache agent classes for 60s


class AgentService:
    """
    Provides functionality to discover and retrieve agent information via NATS-based discovery events.
    `AgentService` acts as the business logic layer for agent operations,
    isolating NATS-based discovery requests from the HTTP layer.
    """

    @staticmethod
    def get_minimal_agent(agent_class: str, agent_id: str, t: LocaleHandler) -> MinimalAgentDTO:
        """Returns minimal details for an agent from database."""
        agent_entity = AgentEntity.get_agent(agent_class=agent_class, agent_id=agent_id)
        return MinimalAgentDTO.from_entity(agent_entity, t)

    @staticmethod
    async def get_agent(nc: NATS, agent_class: str, agent_id: str, t: LocaleHandler) -> AgentDTO:
        """
        Returns details for a given agent. If agent is online, use live information reported by the agent,
        otherwise, use saved information from the database.
        """
        try:
            discovered_agent = await AgentService.discover_agent_instance(nc, agent_class, agent_id)
            return AgentDTO.from_instance(discovered_agent, is_online=True, t=t)
        except HTTPException:
            agent = AgentEntity.get_agent(agent_class, agent_id)
            if agent is None:
                raise HTTPException(status_code=404, detail=f"Agent {agent_class}.{agent_id} not found.")
            return AgentDTO.from_entity(agent, t, is_online=False)

    @staticmethod
    async def get_agents(nc: NATS, t: LocaleHandler) -> list[AgentDTO]:
        """
        Returns both agents that are online (answer to a discovery broadcast) and agents
        that are saved in the database.
        """
        discovered_agents = await AgentService.discover_agents(nc, t)
        saved_agents = [AgentDTO.from_entity(agent, t, is_online=False) for agent in AgentEntity.get_agents()]

        all_agents = discovered_agents.copy()
        for saved_agent in saved_agents:
            was_discovered = (
                len(
                    [
                        a
                        for a in discovered_agents
                        if a.agent_id == saved_agent.agent_id and a.agent_class == saved_agent.agent_class
                    ]
                )
                > 0
            )
            if not was_discovered:
                all_agents.append(saved_agent)

        return all_agents

    @staticmethod
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
                network_graph=WorkflowGraph(directed=True, multigraph=False, graph={}, nodes=[], links=[]),
                is_online=True,
                default_agent_config=event.default_agent_config,
            )
            agent_found_event.set()

        topic_manager = AgentClassTopicManager(agent_class=agent_class)
        nc_publisher = NCPublisher(nc)
        nc_subscriber = AgentNCSubscriber.for_agent_class_discovery_response_events(
            nc, topic_manager, discovery_handler, call_id=call_id
        )
        await nc_subscriber.start()

        # Send discovery request for the specific agent
        await nc_publisher.publish_event(
            event=ClassDiscoveryRequestEvent(),
            subject=topic_manager.get_agent_class_discovery_subject_request(call_id=call_id),
        )

        # Wait up to 1 second for response
        try:
            await asyncio.wait_for(agent_found_event.wait(), timeout=1.0)
        except TimeoutError:
            await nc_subscriber.stop()
            raise HTTPException(status_code=404, detail=f"Agent {agent_class} not found.")

        if agent_class_dto is not None:
            GET_AGENT_CLASS_CACHE[cache_key] = agent_class_dto
            return agent_class_dto

        raise HTTPException(status_code=404, detail=f"Agent {agent_class} not found.")

    @staticmethod
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
        nc_publisher = NCPublisher(nc)
        nc_subscriber = AgentNCSubscriber.for_agent_class_discovery_response_events(
            nc, topic_manager, discovery_handler, call_id=call_id
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
    async def discover_agents(nc: NATS, t: LocaleHandler) -> list[AgentDTO]:
        discovered_agents = await AgentService.discover_agent_instances(nc)
        return [AgentDTO.from_instance(agent_instance, is_online=True, t=t) for agent_instance in discovered_agents]

    @staticmethod
    async def _send_event(
        nc: NATS,
        external_agent_event_distributor: ExternalAgentEventDistributor,
        user: UserIdentity,
        start_event: BaseEvent,
        agent_class: str,
        agent_id: str,
        thread_id: ObjectId | None = None,
        display_id: ObjectId | None = None,
    ) -> StopEvent | ExceptionEvent:
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
            agent_class=agent_class,
            agent_id=agent_id,
            thread_id=str(thread.id),
            display_id=display_id or str(ObjectId()),
            run_id="*",
        )
        external_event = ExternalAgentEvent(
            thread_id=topic_manager.thread_id,
            display_id=topic_manager.display_id,
            event=start_event,
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
    async def send_agent_start_event(
        nc: NATS,
        agent_class: str,
        agent_id: str,
        start_event_parents: list[str],
        start_event_name: str,
        raw_event_data: dict,
        external_agent_event_distributor: ExternalAgentEventDistributor,
        thread_id: ObjectId | None,
        display_id: ObjectId | None,
        user: UserIdentity,
        t: LocaleHandler,
        agent_config: AgentConfig,
    ) -> StopEvent | ExceptionEvent:
        """
        Sends a start event to a specific agent and waits for a response.
        """
        json_data: dict[str, Any] = {
            "event_id": str(ObjectId()),
            "created_at": time.time_ns(),
            "user": user,
            **raw_event_data,
            "locale": t.locale,
            "_parent_event_names": start_event_parents,
            "_event_name": start_event_name,
            "agent_config": agent_config.model_dump(),
        }
        event: StartEvent = StartEvent.deserialize_event(json_data)

        return await AgentService._send_event(
            nc,
            external_agent_event_distributor,
            user,
            event,
            agent_class,
            agent_id,
            thread_id,
            display_id,
        )

    @staticmethod
    async def get_paginated_agent_threads(
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
    def _clear_cache() -> None:
        """
        Clears the in-memory caches used for agent discovery. Useful for testing purposes to ensure fresh discovery
        requests.
        """
        DISCOVER_AGENTS_CACHE.clear()
        GET_AGENT_INSTANCE_CACHE.clear()
        GET_AGENT_CLASS_CACHE.clear()
