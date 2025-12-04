# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.agent.BotInTheLoopAgent.BotInTheLoopAgent import BotInTheLoopAgent
from playground.agent.BotInTheLoopAgent.BotInTheLoopAgentConfig import BotInTheLoopAgentConfig

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=BotInTheLoopAgent,
        default_agent_config=BotInTheLoopAgentConfig(
            agent_id="bot_in_the_loop_agent",
            agent_class=BotInTheLoopAgent.__name__,
            name=LocaleString(en="Bot in the Loop Agent"),
            description=LocaleString(en="This is an agent with the Bot in the Loop"),
        ),
    )

    task = asyncio.create_task(runner.run_forever())

    try:
        await task
    except KeyboardInterrupt:
        task.cancel()
        await task


if __name__ == "__main__":
    asyncio.run(main())
