import asyncio

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events import StartEvent

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.fan_out_workflow.FanOutAgent import FanOutAgent
from playground.minimal_workflow.fan_out_workflow.FanOutAgentConfig import (
    FanOutAgentConfig,
)

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
