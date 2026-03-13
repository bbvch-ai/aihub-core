from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402

from swiss_ai_hub.core.events.agent import StartEvent  # noqa: E402
from swiss_ai_hub.core.i18n import LocaleString  # noqa: E402
from swiss_ai_hub.core.infrastructure import enable_logging  # noqa: E402

from playground.performance.performance_testing_agent.performance_testing_agent import (  # noqa: E402
    PerformanceTestingAgent,
)
from playground.performance.performance_testing_agent.performance_testing_agent_config import (  # noqa: E402
    PerformanceTestingAgentConfig,
)
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner  # noqa: E402

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=PerformanceTestingAgent,
        agent_config=PerformanceTestingAgentConfig(
            agent_id="performance_testing_agent",
            name=LocaleString(en="Performance Testing Agent"),
            description=LocaleString(en=""),
            number_of_events=10,
            payload_kb=0,
        ),
    )

    async with runner.test_run(delay_before_stop=1) as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=StartEvent(),
        )


if __name__ == "__main__":
    asyncio.run(main())
