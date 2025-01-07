import asyncio

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent
from playground.minimal_workflow.displaying_workflow.DisplayingAgent import (
    DisplayingAgent,
)
from playground.minimal_workflow.displaying_workflow.DisplayingAgentConfig import (
    DisplayingAgentConfig,
)


async def main():
    runner = AgentTestRunner(
        agent_type=DisplayingAgent,
        agent_config=DisplayingAgentConfig(
            agent_id="displaying_agent",
            name=LocaleString(en="Displaying Agent"),
            description=LocaleString(
                en="This is a very simple agent that displays stuff to the user"
            ),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic, start_event=StartEvent(messages=[])
        )


if __name__ == "__main__":
    asyncio.run(main())
