import asyncio
from asyncio import sleep

from swiss_ai_hub.core.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from swiss_ai_hub.core.events.agent.hitl.HumanInTheLoopInput import HumanInTheLoopInput
from swiss_ai_hub.core.events.agent.user.UserMessageEvent import UserMessageEvent
from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.topics.agents.PartialAgentTopic import PartialAgentTopic

from playground.minimal_workflow.human_in_the_loop_workflow.HumanInTheLoopAgent import (
    HumanInTheLoopAgent,
)
from playground.minimal_workflow.human_in_the_loop_workflow.HumanInTheLoopAgentConfig import (
    HumanInTheLoopAgentConfig,
)
from swiss_ai_hub.agent.runners.AgentTestRunner import AgentTestRunner


async def main():
    runner = AgentTestRunner(
        agent_type=HumanInTheLoopAgent,
        agent_config=HumanInTheLoopAgentConfig(
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
