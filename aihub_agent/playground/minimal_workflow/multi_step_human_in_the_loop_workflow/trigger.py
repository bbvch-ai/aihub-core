import asyncio
from asyncio import sleep

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic
from playground.minimal_workflow.multi_step_human_in_the_loop_workflow.HumanInTheLoopAgent import (
    MultiStepHumanInTheLoopAgent,
)
from playground.minimal_workflow.multi_step_human_in_the_loop_workflow.HumanInTheLoopAgentConfig import (
    MultiStepHumanInTheLoopAgentConfig,
)
from playground.minimal_workflow.multi_step_human_in_the_loop_workflow.events.FirstStepHumanInTheLoop import (
    FirstStepHumanInTheLoop,
)
from playground.minimal_workflow.multi_step_human_in_the_loop_workflow.events.SecondStepHumanInTheLoop import (
    SecondStepHumanInTheLoop,
)


async def main():
    runner = AgentTestRunner(
        agent_type=MultiStepHumanInTheLoopAgent,
        agent_config=MultiStepHumanInTheLoopAgentConfig(
            agent_id="multi_step_human_in_the_loop_agent",
            name=LocaleString(en="Multi Step Human in the Loop Agent"),
            description=LocaleString(
                en="This is an agent with the Human in the Loop over multiple steps"
            ),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )

    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic, start_event=StartEvent(messages=[])
        )
        await sleep(1)

        first_request_event = FirstStepHumanInTheLoop.request(
            question="Shall I continue?", topic=PartialAgentTopic()
        )
        await runner.send_event_from_topic(
            topic=topic,
            start_event=FirstStepHumanInTheLoop.response(
                response="Yes, Please!", request_event=first_request_event
            ),
        )
        await sleep(1)

        second_request_event = SecondStepHumanInTheLoop.request(
            question="Are you sure?", topic=PartialAgentTopic()
        )
        await runner.send_event_from_topic(
            topic=topic,
            start_event=SecondStepHumanInTheLoop.response(
                response="Yeees, absolutely!", request_event=second_request_event
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
