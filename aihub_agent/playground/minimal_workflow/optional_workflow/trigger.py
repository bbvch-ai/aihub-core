import asyncio

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import UserMessageEvent
from playground.minimal_workflow.optional_workflow.OptionalAgent import OptionalAgent
from playground.minimal_workflow.optional_workflow.OptionalAgentConfig import (
    OptionalAgentConfig,
)


async def main():
    runner = AgentTestRunner(
        agent_type=OptionalAgent,
        agent_config=OptionalAgentConfig(
            agent_id="optional_agent",
            name=LocaleString(en="Optional Agent"),
            description=LocaleString(en="This is an agent with optional input"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )

    async with runner.test_run() as topic:
        await runner.send_event_from_topic(topic=topic, start_event=UserMessageEvent(messages=[]))


if __name__ == "__main__":
    asyncio.run(main())
