from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio

from swiss_ai_hub.core.events.agent import StartEvent
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import enable_logging

from playground.minimal_workflow.conditional_workflow.conditional_agent import (
    ConditionalAgent,
)
from playground.minimal_workflow.conditional_workflow.conditional_agent_config import (
    ConditionalAgentConfig,
)
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=ConditionalAgent,
        agent_config=ConditionalAgentConfig(
            agent_id="conditional_agent",
            agent_class=ConditionalAgent.__name__,
            name=LocaleString(en="Conditional Agent"),
            description=LocaleString(en="This is an agent with conditions"),
        ),
    )
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=StartEvent(),
        )


if __name__ == "__main__":
    asyncio.run(main())
