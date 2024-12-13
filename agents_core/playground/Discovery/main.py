import asyncio

from bson import ObjectId

from agents_core.runners.AgentTestRunner import AgentTestRunner
from lib_core.i18n.LocaleString import LocaleString
from lib_core.nats.events.discovery.DiscoveryRequestEvent import DiscoveryRequestEvent
from lib_core.nats.topic_managers.TopicManager import TopicManager
from lib_core.testing.logging.logger import enable_logging
from playground.Discovery.DiscoverableAgent import DiscoverableAgent
from playground.Discovery.DiscoverableAgentConfig import DiscoverableAgentConfig

enable_logging()

async def main():
    runner = AgentTestRunner(
        agent_type=DiscoverableAgent,
        agent_config=DiscoverableAgentConfig(
            agent_id="discoverable_agent",
            name=LocaleString(en="Discoverable Agent"),
            description=LocaleString(en="This is a very simple discoverable agent"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )

    call_id = str(ObjectId())
    async with runner.test_run() as topic:
        await runner.nc_publisher.publish_event(
            event=DiscoveryRequestEvent(),
            subject=TopicManager().get_agent_discovery_subject_request(call_id=call_id)
        )

if __name__ == "__main__":
    asyncio.run(main())