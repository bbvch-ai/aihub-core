import asyncio
from asyncio import sleep
from typing import List, Optional

from aihub_api.routes.agent.dto.AgentConfigDTO import AgentConfigDTO
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.discovery.AgentDiscoveryResponseEvent import AgentDiscoveryResponseEvent
from aihub_lib.nats.events.discovery.DiscoveryRequestEvent import DiscoveryRequestEvent
from aihub_lib.nats.publishers.NCPublisher import NCPublisher
from aihub_lib.nats.subscribers.NCSubscriber import NCSubscriber
from aihub_lib.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from aihub_lib.nats.topic_managers.TopicManager import TopicManager
from aihub_lib.nats.topics import DiscoveryTopic
from bson import ObjectId
from cachetools import TTLCache
from fastapi import HTTPException
from nats.aio.client import Client as NATS

from aihub_api.routes.agent.dto.AgentDTO import AgentDTO

# In-memory caches to avoid repeatedly querying NATS for agent info
DISCOVER_AGENTS_CACHE = TTLCache(maxsize=1, ttl=60)  # Cache the entire agent list for 60s
GET_AGENT_CACHE = TTLCache(maxsize=100, ttl=60)  # Cache individual agents for 60s


class AgentService:
    """
    Provides functionality to discover and retrieve agent information via NATS-based discovery events.

    ### Why AgentService?
    `AgentService` acts as the business logic layer for agent operations,
    isolating NATS-based discovery requests from the HTTP layer.

    ### Key Operations
    - `discover_agents`: Broadcasts a DiscoveryRequestEvent and collects all AgentDiscoveryResponseEvents,
      returning a list of discovered agents.
    - `get_agent`: Sends a targeted discovery request to identify a specific agent.

    ### Caching
    - Entire agent lists are cached for 60 seconds to reduce NATS load.
    - Individual agent details are also cached for 60 seconds.

    If the agent or agent list isn't found in cache, a new NATS discovery request is performed.
    """

    @staticmethod
    async def discover_agents(nc: NATS, t: LocaleHandler) -> List[AgentDTO]:
        """
        Discovers all agents by broadcasting a discovery request and waiting for responses.
        Returns a cached result if available.
        """
        cache_key = "all_agents"

        if cache_key in DISCOVER_AGENTS_CACHE:
            return DISCOVER_AGENTS_CACHE[cache_key]

        call_id = str(ObjectId())
        discovery_responses = []

        async def discovery_handler(event: AgentDiscoveryResponseEvent, topic: DiscoveryTopic):
            discovery_responses.append(event)

        topic_manager = TopicManager()
        nc_publisher = NCPublisher(nc)
        nc_subscriber = NCSubscriber.for_agent_discovery_response_events(
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

        agents = [
            AgentDTO(
                agent_class=response.agent_class,
                agent_id=response.agent_id,
                agent_config=AgentConfigDTO.from_agent_config(response.agent_config, t),
                is_conversational=response.is_conversational,
                start_events=response.start_events,
                stop_events=response.stop_events,
                network_graph=response.network_graph,
            )
            for response in discovery_responses
        ]

        DISCOVER_AGENTS_CACHE[cache_key] = agents
        return agents

    @staticmethod
    async def get_agent(nc: NATS, agent_class: str, agent_id: str, t: LocaleHandler) -> AgentDTO:
        """
        Retrieves details about a specific agent. If cached, returns immediately.
        Otherwise, sends a targeted discovery request and waits for a response.
        """
        cache_key = (agent_class, agent_id)

        if cache_key in GET_AGENT_CACHE:
            return GET_AGENT_CACHE[cache_key]

        call_id = str(ObjectId())
        agent: Optional[AgentDTO] = None
        agent_found_event = asyncio.Event()

        async def discovery_handler(event: AgentDiscoveryResponseEvent, topic: DiscoveryTopic):
            nonlocal agent
            # Found the agent, stop subscriber and signal event
            await nc_subscriber.stop()
            agent = AgentDTO(
                agent_class=event.agent_class,
                agent_id=event.agent_id,
                agent_config=AgentConfigDTO.from_agent_config(event.agent_config, t),
                is_conversational=event.is_conversational,
                start_events=event.start_events,
                stop_events=event.stop_events,
            )
            agent_found_event.set()

        topic_manager = AgentInstanceTopicManager(agent_class=agent_class, agent_id=agent_id)
        nc_publisher = NCPublisher(nc)
        nc_subscriber = NCSubscriber.for_agent_discovery_response_events(
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
        except asyncio.TimeoutError:
            await nc_subscriber.stop()
            raise HTTPException(status_code=404, detail=f"Agent {agent_class}.{agent_id} not found.")

        if agent is not None:
            GET_AGENT_CACHE[cache_key] = agent
            return agent

        raise HTTPException(status_code=404, detail=f"Agent {agent_class}.{agent_id} not found.")
