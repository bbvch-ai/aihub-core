from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402

from llama_index.core.base.llms.types import ChatMessage, MessageRole  # noqa: E402
from swiss_ai_hub.core.auth import DangerousDevelopmentOnlyAuthSettings  # noqa: E402
from swiss_ai_hub.core.events.agent import UserMessageEvent  # noqa: E402
from swiss_ai_hub.core.i18n import LocaleString  # noqa: E402

from playground.minimal_workflow.bounded_loop.bounded_loop_agent import BoundedLoopAgent  # noqa: E402
from playground.minimal_workflow.bounded_loop.bounded_loop_agent_config import BoundedLoopAgentConfig  # noqa: E402
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner  # noqa: E402


async def main():
    runner = AgentTestRunner(
        agent_type=BoundedLoopAgent,
        agent_config=BoundedLoopAgentConfig(
            agent_id="bounded_iterative_loop_agent",
            name=LocaleString(en="Bounded Iterative Agent"),
            description=LocaleString(en="This is an agent that loops"),
            loop_max=2,
        ),
    )
    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content="Hello", role=MessageRole.USER)],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
