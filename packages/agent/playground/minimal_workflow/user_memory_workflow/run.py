# ruff: noqa: E402
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from swiss_ai_hub.core.generative_ai import LLMConfig, LLMParameter
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.infrastructure import enable_logging

from playground.minimal_workflow.user_memory_workflow.user_memory_agent import UserMemoryAgent
from playground.minimal_workflow.user_memory_workflow.user_memory_agent_config import UserMemoryAgentConfig
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner

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
                model_name="text-generation/gpt-oss-120b",
                default_parameter=LLMParameter(temperature=1.0),
            ),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
