import asyncio

from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import UserMessageEvent

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
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
            agent_class=DisplayingAgent.__name__,
            name=LocaleString(en="Displaying Agent"),
            description=LocaleString(en="This is a very simple agent that displays stuff to the user"),
        ),
    )
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
