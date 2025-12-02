import asyncio

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent
from aihub_lib.infrastructure.logging.logger import enable_logging

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.optional_workflow.OptionalAgent import OptionalAgent
from playground.minimal_workflow.optional_workflow.OptionalAgentConfig import (
    OptionalAgentConfig,
)

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=OptionalAgent,
        default_agent_config=OptionalAgentConfig(
            agent_id="optional_agent",
            agent_class=OptionalAgent.__name__,
            name=LocaleString(en="Optional Agent"),
            description=LocaleString(en="This is an agent with optional input"),
        ),
    )

    async with runner.test_run() as topic:
        await runner.send_event_from_topic(topic=topic, start_event=StartEvent())


if __name__ == "__main__":
    asyncio.run(main())
