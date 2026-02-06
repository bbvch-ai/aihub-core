import asyncio
from asyncio import sleep

from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import UserMessageEvent
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.multistep_human_in_the_loop_workflow.events.FirstStepHumanInTheLoop import (
    FirstStepHumanInTheLoop,
)
from playground.minimal_workflow.multistep_human_in_the_loop_workflow.events.SecondStepHumanInTheLoop import (
    SecondStepHumanInTheLoop,
)
from playground.minimal_workflow.multistep_human_in_the_loop_workflow.MultistepHumanInTheLoopAgent import (
    MultistepHumanInTheLoopAgent,
)
from playground.minimal_workflow.multistep_human_in_the_loop_workflow.MultistepHumanInTheLoopAgentConfig import (
    MultistepHumanInTheLoopAgentConfig,
)


async def main():
    runner = AgentTestRunner(
        agent_type=MultistepHumanInTheLoopAgent,
        agent_config=MultistepHumanInTheLoopAgentConfig(
            agent_id="multistep_human_in_the_loop_agent",
            agent_class=MultistepHumanInTheLoopAgent.__name__,
            name=LocaleString(en="Multistep Human in the Loop Agent"),
            description=LocaleString(en="This is an agent with the Human in the Loop over multiple steps"),
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

        first_request_event = FirstStepHumanInTheLoop.request(question="Shall I continue?", topic=PartialAgentTopic())
        await runner.send_event_from_topic(
            topic=topic,
            start_event=FirstStepHumanInTheLoop.response(response="Yes, Please!", request_event=first_request_event),
        )
        await sleep(1)

        second_request_event = SecondStepHumanInTheLoop.request(question="Are you sure?", topic=PartialAgentTopic())
        await runner.send_event_from_topic(
            topic=topic,
            start_event=SecondStepHumanInTheLoop.response(
                response="Yeees, absolutely!", request_event=second_request_event
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
