from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402
from asyncio import sleep  # noqa: E402

from swiss_ai_hub.core.events.agent import UserMessageEvent  # noqa: E402
from swiss_ai_hub.core.i18n import LocaleString  # noqa: E402
from swiss_ai_hub.core.testing.auth_utils import fake_user  # noqa: E402
from swiss_ai_hub.core.topics import PartialAgentTopic  # noqa: E402

from playground.minimal_workflow.multistep_human_in_the_loop_workflow.events.first_step_human_in_the_loop import (  # noqa: E402
    FirstStepHumanInTheLoop,
)
from playground.minimal_workflow.multistep_human_in_the_loop_workflow.events.second_step_human_in_the_loop import (  # noqa: E402
    SecondStepHumanInTheLoop,
)
from playground.minimal_workflow.multistep_human_in_the_loop_workflow.multistep_human_in_the_loop_agent import (  # noqa: E402
    MultistepHumanInTheLoopAgent,
)
from playground.minimal_workflow.multistep_human_in_the_loop_workflow.multistep_human_in_the_loop_agent_config import (  # noqa: E402
    MultistepHumanInTheLoopAgentConfig,
)
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner  # noqa: E402


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
                user=fake_user(),
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
