import asyncio
from asyncio import sleep

from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import UserMessageEvent
from aihub_lib.nats.events.human_in_the_loop.HumanInTheLoop import HumanInTheLoopChat
from aihub_lib.nats.topics.agents.PartialAgentTopic import PartialAgentTopic

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.hitl_demo_workflow.HitlDemoAgent import (
    HitlDemoAgent,
    HitlTypeSelection,
)
from playground.minimal_workflow.hitl_demo_workflow.HitlDemoAgentConfig import HitlDemoAgentConfig


async def main():
    runner = AgentTestRunner(
        agent_type=HitlDemoAgent,
        default_agent_config=HitlDemoAgentConfig(
            agent_id="hitl_demo_agent",
            agent_class=HitlDemoAgent.__name__,
            name=LocaleString(en="HITL Demo Agent"),
            description=LocaleString(en="Demo agent showcasing all HITL types"),
        ),
    )

    async with runner.test_run() as topic:
        # Start the workflow
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
            ),
        )
        await sleep(1)

        # Respond to first HITL: choose "chat" type (using custom HitlTypeSelection)
        first_request = HitlTypeSelection.request(
            question="Which HITL type would you like to test?",
            topic=PartialAgentTopic(),
        )
        await runner.send_event_from_topic(
            topic=topic,
            start_event=HitlTypeSelection.response(
                response="chat",
                request_event=first_request,
            ),
        )
        await sleep(1)

        # Respond to second HITL: chat response
        second_request = HumanInTheLoopChat.request(
            question="This is a chat-style question.",
            topic=PartialAgentTopic(),
        )
        await runner.send_event_from_topic(
            topic=topic,
            start_event=HumanInTheLoopChat.response(
                response="This is my chat response!",
                request_event=second_request,
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
