import asyncio
from asyncio import sleep

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import UserMessageEvent
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic
from aihub_lib.testing.auth_utils.fake_user import fake_user

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
            name=LocaleString(en="Multistep Human in the Loop Agent"),
            description=LocaleString(en="This is an agent with the Human in the Loop over multiple steps"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )

    async with runner.test_run() as topic:
        await runner.send_event_from_topic(topic=topic, start_event=UserMessageEvent(messages=[], user=fake_user()))
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
