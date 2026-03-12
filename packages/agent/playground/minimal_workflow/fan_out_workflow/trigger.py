from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio

from swiss_ai_hub.core.events.agent import StartEvent
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import enable_logging

from playground.minimal_workflow.fan_out_workflow.fan_out_agent import FanOutAgent
from playground.minimal_workflow.fan_out_workflow.fan_out_agent_config import (
    FanOutAgentConfig,
)
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=FanOutAgent,
        agent_config=FanOutAgentConfig(
            agent_id="fan_out_agent",
            name=LocaleString(en="Fan Out Agent"),
            description=LocaleString(en="This is an agent that fans out multiple steps"),
        ),
    )
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(topic=topic, start_event=StartEvent())


if __name__ == "__main__":
    asyncio.run(main())
