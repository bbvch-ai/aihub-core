from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio

from swiss_ai_hub.core.events.agent import StartEvent
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import enable_logging

from playground.minimal_workflow.optional_workflow.optional_agent import OptionalAgent
from playground.minimal_workflow.optional_workflow.optional_agent_config import (
    OptionalAgentConfig,
)
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=OptionalAgent,
        agent_config=OptionalAgentConfig(
            agent_id="optional_agent",
            name=LocaleString(en="Optional Agent"),
            description=LocaleString(en="This is an agent with optional input"),
        ),
    )

    async with runner.test_run() as topic:
        await runner.send_event_from_topic(topic=topic, start_event=StartEvent())


if __name__ == "__main__":
    asyncio.run(main())
