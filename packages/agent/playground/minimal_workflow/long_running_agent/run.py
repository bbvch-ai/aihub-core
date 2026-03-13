from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402

from swiss_ai_hub.core.i18n import LocaleString  # noqa: E402
from swiss_ai_hub.core.infrastructure import enable_logging  # noqa: E402

from playground.minimal_workflow.long_running_agent.long_running_agent import LongRunningAgent  # noqa: E402
from playground.minimal_workflow.long_running_agent.long_running_agent_config import (  # noqa: E402
    LongRunningAgentConfig,
)
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner  # noqa: E402

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=LongRunningAgent,
        agent_config=LongRunningAgentConfig(
            agent_id="long_running",
            name=LocaleString(en="Long Running Agent"),
            description=LocaleString(en="This is an agent that is running looooong"),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
