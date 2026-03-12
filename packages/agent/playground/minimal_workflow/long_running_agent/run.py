from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio

from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import enable_logging

from playground.minimal_workflow.long_running_agent.long_running_agent import LongRunningAgent
from playground.minimal_workflow.long_running_agent.long_running_agent_config import LongRunningAgentConfig
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

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
