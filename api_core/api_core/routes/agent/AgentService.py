import asyncio
from asyncio import sleep
from typing import List, Optional

from bson import ObjectId
from fastapi import HTTPException
from nats.aio.client import Client as NATS
from cachetools import TTLCache

from api_core.routes.agent.dto.AgentDTO import AgentDTO
from lib_core.nats.events.discovery.DiscoveryRequestEvent import DiscoveryRequestEvent
from lib_core.nats.events.discovery.AgentDiscoveryResponseEvent import AgentDiscoveryResponseEvent
from lib_core.nats.publishers.NCPublisher import NCPublisher
from lib_core.nats.subscribers.NCSubscriber import NCSubscriber
from lib_core.nats.topic_managers.TopicManager import TopicManager
from lib_core.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from lib_core.nats.topics import DiscoveryTopic

# Create two caches:
# 1. A cache for the list of all agents discovered by `discover_agents`
# 2. A cache for individual agents discovered by `get_agent`
DISCOVER_AGENTS_CACHE = TTLCache(maxsize=1, ttl=60)  # Cache the entire agent list for 60s
GET_AGENT_CACHE = TTLCache(maxsize=100, ttl=60)  # Cache individual agents for 60s


class AgentService:

    @staticmethod
    async def discover_agents(nc: NATS) -> List[AgentDTO]:
        cache_key = "all_agents"

        # If we have cached results and they haven't expired, return them
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

        await nc_publisher.publish_event(
            event=DiscoveryRequestEvent(),
            subject=topic_manager.get_agent_discovery_subject_request(call_id=call_id)
        )

        await sleep(1)
        await nc_subscriber.stop()

        agents = [
            AgentDTO(
                agent_class=response.agent_class,
                agent_id=response.agent_id,
                agent_config=response.agent_config,
                start_events=response.start_events,
            )
            for response in discovery_responses
        ]

        # Store the discovered agents in the cache
        DISCOVER_AGENTS_CACHE[cache_key] = agents
        return agents

    @staticmethod
    async def get_agent(nc: NATS, agent_class: str, agent_id: str) -> AgentDTO:
        cache_key = (agent_class, agent_id)

        # If we have a cached agent and it hasn't expired, return it
        if cache_key in GET_AGENT_CACHE:
            return GET_AGENT_CACHE[cache_key]

        call_id = str(ObjectId())
        agent: Optional[AgentDTO] = None

        # Create an event to signal when the agent is discovered
        agent_found_event = asyncio.Event()

        async def discovery_handler(event: AgentDiscoveryResponseEvent, topic: DiscoveryTopic):
            nonlocal agent
            # Stop the subscriber since we got our response
            await nc_subscriber.stop()
            agent = AgentDTO(
                agent_class=event.agent_class,
                agent_id=event.agent_id,
                agent_config=event.agent_config,
                start_events=event.start_events,
            )
            # Signal that we have found the agent
            agent_found_event.set()

        topic_manager = AgentInstanceTopicManager(agent_class=agent_class, agent_id=agent_id)

        nc_publisher = NCPublisher(nc)
        nc_subscriber = NCSubscriber.for_agent_discovery_response_events(
            nc, topic_manager, discovery_handler, call_id=call_id
        )
        await nc_subscriber.start()

        # Publish the discovery request
        await nc_publisher.publish_event(
            event=DiscoveryRequestEvent(),
            subject=topic_manager.get_agent_discovery_subject_request(call_id=call_id)
        )

        # Await the agent_found_event with a timeout
        try:
            await asyncio.wait_for(agent_found_event.wait(), timeout=1.0)
        except asyncio.TimeoutError:
            # Stop the subscriber if still running
            await nc_subscriber.stop()
            raise HTTPException(status_code=404, detail=f"Agent {agent_class}.{agent_id} not found.")

        # If we're here, we have the agent
        if agent is not None:
            # Store in the cache for 60 seconds
            GET_AGENT_CACHE[cache_key] = agent
            return agent

        raise HTTPException(status_code=404, detail=f"Agent {agent_class}.{agent_id} not found.")
