import asyncio

from bson import ObjectId
from swiss_ai_hub.core.events import ClassDiscoveryRequestEvent
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import enable_logging
from swiss_ai_hub.core.topic_managers import AgentTopicManager

from playground.minimal_workflow.discoverable_workflow.DiscoverableAgent import (
    DiscoverableAgent,
)
from playground.minimal_workflow.discoverable_workflow.DiscoverableAgentConfig import (
    DiscoverableAgentConfig,
)
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=DiscoverableAgent,
        agent_config=DiscoverableAgentConfig(
            agent_id="discoverable_agent",
            agent_class=DiscoverableAgent.__name__,
            name=LocaleString(en="Discoverable Agent"),
            description=LocaleString(en="This is a very simple discoverable agent"),
        ),
    )

    call_id = str(ObjectId())
    async with runner.test_run():
        await runner.nc_publisher.publish_event(
            event=ClassDiscoveryRequestEvent(),
            subject=AgentTopicManager().get_agent_class_discovery_subject_request(call_id=call_id),
        )


if __name__ == "__main__":
    asyncio.run(main())
