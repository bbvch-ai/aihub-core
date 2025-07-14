import asyncio
from asyncio import sleep

from aihub_lib.agents.visualizers.types.WorkflowGraph import WorkflowGraph
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.distributor.events.ExternalAgentEvent import ExternalAgentEvent
from aihub_lib.nats.distributor.ExternalAgentEventDistributor import ExternalAgentEventDistributor
from aihub_lib.nats.events import BaseEvent, ExceptionEvent, StopEvent
from aihub_lib.nats.events.discovery.agent.AgentDiscoveryResponseEvent import AgentDiscoveryResponseEvent
from aihub_lib.nats.events.discovery.DiscoveryRequestEvent import DiscoveryRequestEvent
from aihub_lib.nats.publishers.NCPublisher import NCPublisher
from aihub_lib.nats.subscribers.agent.AgentNCSubscriber import AgentNCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from aihub_lib.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.nats.topics.discovery.agent.AgentDiscoveryTopic import AgentDiscoveryTopic
from aihub_lib.persistence.agents.AgentEntity import AgentEntity
from aihub_lib.persistence.messaging.entities.ThreadEntity import Agent, ThreadEntity, User
from aihub_lib.routes.chat.ChatService import ChatService, JsonResources
from bson import ObjectId
from cachetools import TTLCache
from fastapi import HTTPException
from nats.aio.client import Client as NATS

from aihub_api.routes.agent.dto.AgentConfigDTO import AgentConfigDTO
from aihub_api.routes.agent.dto.AgentDTO import AgentDTO, MinimalAgentDTO
from aihub_api.routes.thread.dto.ThreadDTO import ThreadDTO
from aihub_api.routes.thread.ThreadService import ThreadService

# In-memory caches to avoid repeatedly querying NATS for agent info
DISCOVER_AGENTS_CACHE = TTLCache(maxsize=100, ttl=60)  # Cache the entire agent list for 60s
GET_AGENT_CACHE = TTLCache(maxsize=100, ttl=60)  # Cache individual agents for 60s


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
            return await AgentService.discover_agent(nc, agent_class, agent_id, t)
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
    async def discover_agent(nc: NATS, agent_class: str, agent_id: str, t: LocaleHandler) -> AgentDTO:
        """
        Retrieves details about a specific agent. If cached, returns immediately.
        Otherwise, sends a targeted discovery request and waits for a response.
        """
        cache_key = (agent_class, agent_id)

        if cache_key in GET_AGENT_CACHE:
            return GET_AGENT_CACHE[cache_key]

        call_id = str(ObjectId())
        agent_dto: AgentDTO | None = None
        agent_found_event = asyncio.Event()

        async def discovery_handler(event: AgentDiscoveryResponseEvent, topic: AgentDiscoveryTopic):
            nonlocal agent_dto
            # Found the agent, stop subscriber and signal event
            await nc_subscriber.stop()
            agent_dto = AgentDTO(
                agent_class=event.agent_class,
                agent_id=event.agent_id,
                agent_config=AgentConfigDTO.from_agent_config(event.agent_config, t),
                is_conversational=event.is_conversational,
                start_events=event.start_events,
                stop_events=event.stop_events,
                network_graph=WorkflowGraph(directed=True, multigraph=False, graph={}, nodes=[], links=[]),
                is_online=True,
            )
            AgentEntity.create_or_update_from_dto(agent_dto)
            agent_found_event.set()

        topic_manager = AgentInstanceTopicManager(agent_class=agent_class, agent_id=agent_id)
        nc_publisher = NCPublisher(nc)
        nc_subscriber = AgentNCSubscriber.for_agent_discovery_response_events(
            nc, topic_manager, discovery_handler, call_id=call_id
        )
        await nc_subscriber.start()

        # Send discovery request for the specific agent
        await nc_publisher.publish_event(
            event=DiscoveryRequestEvent(), subject=topic_manager.get_agent_discovery_subject_request(call_id=call_id)
        )

        # Wait up to 1 second for response
        try:
            await asyncio.wait_for(agent_found_event.wait(), timeout=1.0)
        except TimeoutError:
            await nc_subscriber.stop()
            raise HTTPException(status_code=404, detail=f"Agent {agent_class}.{agent_id} not found.")

        if agent_dto is not None:
            GET_AGENT_CACHE[cache_key] = agent_dto
            return agent_dto

        raise HTTPException(status_code=404, detail=f"Agent {agent_class}.{agent_id} not found.")

    @staticmethod
    async def discover_agents(nc: NATS, t: LocaleHandler) -> list[AgentDTO]:
        """
        Discovers all agents by broadcasting a discovery request and waiting for responses.
        Returns a cached result if available.
        """
        cache_key = "all_agents"

        if cache_key in DISCOVER_AGENTS_CACHE:
            return DISCOVER_AGENTS_CACHE[cache_key]

        call_id = str(ObjectId())
        discovery_responses = []

        async def discovery_handler(event: AgentDiscoveryResponseEvent, topic: AgentDiscoveryTopic):
            discovery_responses.append(event)

        topic_manager = AgentTopicManager()
        nc_publisher = NCPublisher(nc)
        nc_subscriber = AgentNCSubscriber.for_agent_discovery_response_events(
            nc, topic_manager, discovery_handler, call_id=call_id
        )
        await nc_subscriber.start()

        # Broadcast the discovery request
        await nc_publisher.publish_event(
            event=DiscoveryRequestEvent(), subject=topic_manager.get_agent_discovery_subject_request(call_id=call_id)
        )

        # Wait briefly for responses
        await sleep(1)
        await nc_subscriber.stop()

        unique_agents_dict = {}

        for response in discovery_responses:
            unique_key = (response.agent_class, response.agent_id)

            if unique_key not in unique_agents_dict:
                agent_dto = AgentDTO(
                    agent_class=response.agent_class,
                    agent_id=response.agent_id,
                    agent_config=AgentConfigDTO.from_agent_config(response.agent_config, t),
                    is_conversational=response.is_conversational,
                    start_events=response.start_events,
                    stop_events=response.stop_events,
                    network_graph=response.network_graph,
                    is_online=True,
                )
                AgentEntity.create_or_update_from_dto(agent_dto)
                unique_agents_dict[unique_key] = agent_dto

        agents = list(unique_agents_dict.values())

        if len(agents) > 0:
            DISCOVER_AGENTS_CACHE[cache_key] = agents

        return agents

    @staticmethod
    async def send_event(
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
    def clear_cache() -> None:
        """
        Clears the in-memory caches used for agent discovery. Useful for testing purposes to ensure fresh discovery
        requests.
        """
        DISCOVER_AGENTS_CACHE.clear()
        GET_AGENT_CACHE.clear()
