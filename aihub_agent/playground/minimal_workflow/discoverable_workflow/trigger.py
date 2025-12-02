import asyncio

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.discovery.InstanceDiscoveryRequestEvent import InstanceDiscoveryRequestEvent
from aihub_lib.nats.topic_managers.agents.AgentTopicManager import AgentTopicManager
from aihub_lib.infrastructure.logging.logger import enable_logging
from bson import ObjectId

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
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
        default_agent_config=DiscoverableAgentConfig(
            agent_id="discoverable_agent",
            agent_class=DiscoverableAgent.__name__,
            name=LocaleString(en="Discoverable Agent"),
            description=LocaleString(en="This is a very simple discoverable agent"),
        ),
    )

    call_id = str(ObjectId())
    async with runner.test_run():
        await runner.nc_publisher.publish_event(
            event=InstanceDiscoveryRequestEvent(),
            subject=AgentTopicManager().get_agent_instance_discovery_subject_request(call_id=call_id),
        )


if __name__ == "__main__":
    asyncio.run(main())
