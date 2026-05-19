# ruff: noqa: E402
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip  # noqa: E402

AihubInstrumentor().instrument()

import asyncio  # noqa: E402

from swiss_ai_hub.core.generative_ai import LLMConfig, LLMParameter  # noqa: E402
from swiss_ai_hub.core.i18n import LocaleString  # noqa: E402
from swiss_ai_hub.core.infrastructure import enable_logging  # noqa: E402

from playground.minimal_workflow.user_memory_workflow.user_memory_agent import UserMemoryAgent  # noqa: E402
from playground.minimal_workflow.user_memory_workflow.user_memory_agent_config import (  # noqa: E402
    UserMemoryAgentConfig,
)
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner  # noqa: E402

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=UserMemoryAgent,
        agent_config=UserMemoryAgentConfig(
            agent_class=UserMemoryAgent.__name__,
            agent_id="memory_agent",
            name=LocaleString(en="User Memory Agent"),
            description=LocaleString(en="This is the Memory Agent config"),
            llm=LLMConfig(
                model_name="text-generation/Qwen3-VL-235B-A22B-Instruct",
                default_parameter=LLMParameter(temperature=1.0),
            ),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
