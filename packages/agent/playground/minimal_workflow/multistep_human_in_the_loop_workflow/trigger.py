from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio
from asyncio import sleep

from swiss_ai_hub.core.auth import DangerousDevelopmentOnlyAuthSettings
from swiss_ai_hub.core.events.agent import UserMessageEvent
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.topics import PartialAgentTopic

from playground.minimal_workflow.multistep_human_in_the_loop_workflow.events.first_step_human_in_the_loop import (
    FirstStepHumanInTheLoop,
)
from playground.minimal_workflow.multistep_human_in_the_loop_workflow.events.second_step_human_in_the_loop import (
    SecondStepHumanInTheLoop,
)
from playground.minimal_workflow.multistep_human_in_the_loop_workflow.multistep_human_in_the_loop_agent import (
    MultistepHumanInTheLoopAgent,
)
from playground.minimal_workflow.multistep_human_in_the_loop_workflow.multistep_human_in_the_loop_agent_config import (
    MultistepHumanInTheLoopAgentConfig,
)
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner


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
