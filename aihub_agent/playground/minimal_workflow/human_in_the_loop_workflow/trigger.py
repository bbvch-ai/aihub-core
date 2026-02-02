import asyncio
from asyncio import sleep

from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import UserMessageEvent
from aihub_lib.nats.events.human_in_the_loop import HumanInTheLoopInput
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.human_in_the_loop_workflow.HumanInTheLoopAgent import (
    HumanInTheLoopAgent,
)
from playground.minimal_workflow.human_in_the_loop_workflow.HumanInTheLoopAgentConfig import (
    HumanInTheLoopAgentConfig,
)


async def main():
    runner = AgentTestRunner(
        agent_type=HumanInTheLoopAgent,
        default_agent_config=HumanInTheLoopAgentConfig(
            agent_id="human_in_the_loop_agent",
            agent_class=HumanInTheLoopAgent.__name__,
            name=LocaleString(en="Human in the Loop Agent"),
            description=LocaleString(en="This is an agent with the Human in the Loop"),
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
        await sleep(1)
        request_event = HumanInTheLoopInput.request(question="Shall I continue?", topic=PartialAgentTopic())
        await runner.send_event_from_topic(
            topic=topic,
            start_event=HumanInTheLoopInput.response(response="Yes, Please!", request_event=request_event),
        )


if __name__ == "__main__":
    asyncio.run(main())
