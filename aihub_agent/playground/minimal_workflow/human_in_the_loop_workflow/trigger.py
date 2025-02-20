import asyncio
from asyncio import sleep

from aihub_lib.nats.events.human_in_the_loop.HumanInTheLoop import HumanInTheLoop

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent, UserMessageEvent
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic
from playground.minimal_workflow.human_in_the_loop_workflow.HumanInTheLoopAgent import (
    HumanInTheLoopAgent,
)
from playground.minimal_workflow.human_in_the_loop_workflow.HumanInTheLoopAgentConfig import (
    HumanInTheLoopAgentConfig,
)


async def main():
    runner = AgentTestRunner(
        agent_type=HumanInTheLoopAgent,
        agent_config=HumanInTheLoopAgentConfig(
            agent_id="human_in_the_loop_agent",
            name=LocaleString(en="Human in the Loop Agent"),
            description=LocaleString(en="This is an agent with the Human in the Loop"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )

    async with runner.test_run() as topic:
        await runner.send_event_from_topic(topic=topic, start_event=UserMessageEvent(messages=[]))
        await sleep(1)
        request_event = HumanInTheLoop.request(question="Shall I continue?", topic=PartialAgentTopic())
        await runner.send_event_from_topic(
            topic=topic,
            start_event=HumanInTheLoop.response(response="Yes, Please!", request_event=request_event),
        )


if __name__ == "__main__":
    asyncio.run(main())
