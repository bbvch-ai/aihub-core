from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402

from swiss_ai_hub.core.auth import DangerousDevelopmentOnlyAuthSettings  # noqa: E402
from swiss_ai_hub.core.events.agent import UserMessageEvent  # noqa: E402
from swiss_ai_hub.core.generative_ai import LLMConfig, LLMParameter  # noqa: E402
from swiss_ai_hub.core.i18n import LocaleString  # noqa: E402

from playground.minimal_workflow.user_memory_workflow.user_memory_agent import UserMemoryAgent  # noqa: E402
from playground.minimal_workflow.user_memory_workflow.user_memory_agent_config import (  # noqa: E402
    UserMemoryAgentConfig,
)
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner  # noqa: E402


async def main():
    """One-shot test runner for UserMemoryAgent."""
    runner = AgentTestRunner(
        agent_type=UserMemoryAgent,
        agent_config=UserMemoryAgentConfig(
            agent_class=UserMemoryAgent.__name__,
            agent_id="memory_agent",
            name=LocaleString(en="User Memory Agent"),
            description=LocaleString(en="This is the Memory Agent config"),
            llm=LLMConfig(
                model_name="text-generation/gpt-oss-120b",
                default_parameter=LLMParameter(temperature=1.0),
            ),
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


if __name__ == "__main__":
    asyncio.run(main())
