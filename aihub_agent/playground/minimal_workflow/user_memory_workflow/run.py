# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig, LLMParameter
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.user_memory_workflow.UserMemoryAgent import UserMemoryAgent
from playground.minimal_workflow.user_memory_workflow.UserMemoryAgentConfig import UserMemoryAgentConfig

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=UserMemoryAgent,
        default_agent_config=UserMemoryAgentConfig(
            agent_class=UserMemoryAgent.__name__,
            agent_id="memory_agent",
            name=LocaleString(en="User Memory Agent"),
            description=LocaleString(en="This is the Memory Agent config"),
            llm=LLMConfig(model_name="text-generation/gemma-3n-e4b", default_parameter=LLMParameter(temperature=1.0)),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
