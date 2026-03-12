# ruff: noqa: E402
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import enable_logging

from playground.agent.bot_in_the_loop_agent.bot_in_the_loop_agent import BotInTheLoopAgent
from playground.agent.bot_in_the_loop_agent.bot_in_the_loop_agent_config import BotInTheLoopAgentConfig
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=BotInTheLoopAgent,
        agent_config=BotInTheLoopAgentConfig(
            agent_id="bot_in_the_loop_agent",
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
