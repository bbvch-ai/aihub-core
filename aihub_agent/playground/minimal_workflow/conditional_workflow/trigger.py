import asyncio

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events import StartEvent

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.conditional_workflow.ConditionalAgent import (
    ConditionalAgent,
)
from playground.minimal_workflow.conditional_workflow.ConditionalAgentConfig import (
    ConditionalAgentConfig,
)

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=ConditionalAgent,
        default_agent_config=ConditionalAgentConfig(
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
