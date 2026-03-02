import asyncio

from aihub_lib.i18n.LocaleString import LocaleString

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.context_workflow.ContextAgent import ContextAgent
from playground.minimal_workflow.context_workflow.ContextAgentConfig import (
    ContextAgentConfig,
)
from playground.minimal_workflow.context_workflow.events.CustomStartEvent import (
    CustomStartEvent,
)

THREAD_ID = "6756ddb05c399b888009a559"


async def main():
    runner = AgentTestRunner(
        agent_type=ContextAgent,
        agent_config=ContextAgentConfig(
            agent_id="context_agent",
            name=LocaleString(en="Context Agent"),
            description=LocaleString(en="This is an agent that accesses the run and thread context"),
        ),
    )

    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=CustomStartEvent(
                payload="This is some payload",
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
