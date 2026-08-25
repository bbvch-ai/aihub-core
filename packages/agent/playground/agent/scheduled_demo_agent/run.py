# ruff: noqa: E402
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip  # noqa: E402

AihubInstrumentor().instrument()

import asyncio  # noqa: E402

from swiss_ai_hub.core.infrastructure import enable_logging  # noqa: E402

from playground.agent.scheduled_demo_agent.scheduled_demo_agent import ScheduledDemoAgent  # noqa: E402
from playground.agent.scheduled_demo_agent.scheduled_demo_agent_config import (  # noqa: E402
    ScheduledDemoAgentConfig,
)
from swiss_ai_hub.agent.runners.agent_runner import AgentRunner  # noqa: E402

enable_logging()


async def main():
    # The production runner, not AgentTestRunner: the scheduler only fires for classes that discovery
    # has reported as online and schedulable, which requires responding to discovery requests.
    runner = AgentRunner(
        agent_type=ScheduledDemoAgent,
        agent_config=ScheduledDemoAgentConfig.as_form(),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
