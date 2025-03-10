import asyncio

from bson import ObjectId

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.discovery.DiscoveryRequestEvent import DiscoveryRequestEvent
from aihub_lib.nats.topic_managers.TopicManager import TopicManager
from aihub_lib.testing.logging.logger import enable_logging
from playground.minimal_workflow.discoverable_workflow.DiscoverableAgent import (
    DiscoverableAgent,
)
from playground.minimal_workflow.discoverable_workflow.DiscoverableAgentConfig import (
    DiscoverableAgentConfig,
)

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
    async with runner.test_run():
        await runner.nc_publisher.publish_event(
            event=DiscoveryRequestEvent(),
            subject=TopicManager().get_agent_discovery_subject_request(call_id=call_id),
        )


if __name__ == "__main__":
    asyncio.run(main())
