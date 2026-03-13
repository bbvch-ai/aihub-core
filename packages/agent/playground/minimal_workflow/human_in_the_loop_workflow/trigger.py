from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402
from asyncio import sleep  # noqa: E402

from swiss_ai_hub.core.auth import DangerousDevelopmentOnlyAuthSettings  # noqa: E402
from swiss_ai_hub.core.events.agent import HumanInTheLoopInput, UserMessageEvent  # noqa: E402
from swiss_ai_hub.core.i18n import LocaleString  # noqa: E402
from swiss_ai_hub.core.topics import PartialAgentTopic  # noqa: E402

from playground.minimal_workflow.human_in_the_loop_workflow.human_in_the_loop_agent import (  # noqa: E402
    HumanInTheLoopAgent,
)
from playground.minimal_workflow.human_in_the_loop_workflow.human_in_the_loop_agent_config import (  # noqa: E402
    HumanInTheLoopAgentConfig,
)
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner  # noqa: E402


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
