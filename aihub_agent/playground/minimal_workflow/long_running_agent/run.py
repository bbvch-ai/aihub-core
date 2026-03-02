import asyncio

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.long_running_agent.LongRunningAgent import LongRunningAgent
from playground.minimal_workflow.long_running_agent.LongRunningAgentConfig import LongRunningAgentConfig

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
