# ruff: noqa: E402
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip  # noqa: E402

AihubInstrumentor().instrument()

import asyncio  # noqa: E402

from swiss_ai_hub.core.agents import AgentConfig  # noqa: E402
from swiss_ai_hub.core.infrastructure import enable_logging  # noqa: E402

from playground.agent.cron_demo_agent.cron_demo_agent import CronDemoAgent  # noqa: E402
from swiss_ai_hub.agent.runners.agent_runner import AgentRunner  # noqa: E402

enable_logging()


async def main():
    # The production runner, not AgentTestRunner: the scheduler only fires for classes that discovery
    # has reported as online and schedulable, which requires responding to discovery requests.
    # A plain AgentConfig is enough: `cron` lives on the base and the runner injects the element for
    # schedulable classes, so a demo of scheduling needs no config subclass at all.
    runner = AgentRunner(
        agent_type=CronDemoAgent,
        agent_config=AgentConfig.as_form(),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
