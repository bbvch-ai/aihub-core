from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402

from swiss_ai_hub.core.i18n import LocaleString  # noqa: E402

from playground.minimal_workflow.context_workflow.context_agent import ContextAgent  # noqa: E402
from playground.minimal_workflow.context_workflow.context_agent_config import (  # noqa: E402
    ContextAgentConfig,
)
from playground.minimal_workflow.context_workflow.events.custom_start_event import (  # noqa: E402
    CustomStartEvent,
)
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner  # noqa: E402

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
