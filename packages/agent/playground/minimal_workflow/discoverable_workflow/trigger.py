from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402

from bson import ObjectId  # noqa: E402
from swiss_ai_hub.core.events import ClassDiscoveryRequestEvent  # noqa: E402
from swiss_ai_hub.core.i18n import LocaleString  # noqa: E402
from swiss_ai_hub.core.infrastructure import enable_logging  # noqa: E402
from swiss_ai_hub.core.topic_managers import AgentTopicManager  # noqa: E402

from playground.minimal_workflow.discoverable_workflow.discoverable_agent import (  # noqa: E402
    DiscoverableAgent,
)
from playground.minimal_workflow.discoverable_workflow.discoverable_agent_config import (  # noqa: E402
    DiscoverableAgentConfig,
)
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner  # noqa: E402

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
