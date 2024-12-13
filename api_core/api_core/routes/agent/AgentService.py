from asyncio import sleep
from typing import List

from bson import ObjectId
from fastapi import HTTPException
from nats.aio.client import Client as NATS

from api_core.routes.agent.dto.AgentDTO import AgentDTO
from lib_core.nats.events.discovery.DiscoveryRequestEvent import DiscoveryRequestEvent
from lib_core.nats.events.discovery.AgentDiscoveryResponseEvent import AgentDiscoveryResponseEvent
from lib_core.nats.publishers.NCPublisher import NCPublisher
from lib_core.nats.subscribers.NCSubscriber import NCSubscriber
from lib_core.nats.topic_managers.TopicManager import TopicManager
from lib_core.nats.topic_managers.agents.AgentInstanceTopicManager import AgentInstanceTopicManager
from lib_core.nats.topics import DiscoveryTopic


class AgentService:

    @staticmethod
    async def discover_agents(nc: NATS) -> List[AgentDTO]:
        call_id = str(ObjectId())

        discovery_responses = []
        async def discovery_handler(event: AgentDiscoveryResponseEvent, topic: DiscoveryTopic):
            discovery_responses.append(event)

        topic_manager = TopicManager()

        nc_publisher = NCPublisher(nc)
        nc_subscriber = NCSubscriber.for_agent_discovery_response_events(nc, topic_manager, discovery_handler, call_id=call_id)
        await nc_subscriber.start()

        await nc_publisher.publish_event(
            event=DiscoveryRequestEvent(),
            subject=topic_manager.get_agent_discovery_subject_request(call_id=call_id)
        )

        await sleep(1)

        await nc_subscriber.stop()

        return [
            AgentDTO(
                agent_class=response.agent_class,
                agent_id=response.agent_id,
                agent_config=response.agent_config,
                start_events=response.start_events,
            )
            for response in discovery_responses
        ]

    @staticmethod
    async def get_agent(nc: NATS, agent_class: str, agent_id: str) -> AgentDTO:
        call_id = str(ObjectId())

        agent: AgentDTO | None = None

        async def discovery_handler(event: AgentDiscoveryResponseEvent, topic: DiscoveryTopic):
            await nc_subscriber.stop()
            nonlocal agent
            agent = AgentDTO(
                agent_class=event.agent_class,
                agent_id=event.agent_id,
                agent_config=event.agent_config,
                start_events=event.start_events,
            )

        topic_manager = AgentInstanceTopicManager(agent_class=agent_class, agent_id=agent_id)

        nc_publisher = NCPublisher(nc)
        nc_subscriber = NCSubscriber.for_agent_discovery_response_events(nc, topic_manager, discovery_handler, call_id=call_id)
        await nc_subscriber.start()

        await nc_publisher.publish_event(
            event=DiscoveryRequestEvent(),
            subject=topic_manager.get_agent_discovery_subject_request(call_id=call_id)
        )

        await sleep(1)

        await nc_subscriber.stop()

        if agent:
            return agent

        raise HTTPException(status_code=404, detail="Agent not found.")

