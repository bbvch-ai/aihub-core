# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig, LLMParameter
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging

from aihub_agent.agents.LLMWrappingAgent.LLMWrappingAgent import LLMWrappingAgent
from aihub_agent.agents.LLMWrappingAgent.LLMWrappingAgentConfig import LLMWrappingAgentConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=LLMWrappingAgent,
        default_agent_config=LLMWrappingAgentConfig(
            agent_class=LLMWrappingAgent.__name__,
            agent_id="dev_agent",
            name=LocaleString(en="Dev Agent"),
            description=LocaleString(en="This is the default Dev Agent config"),
            llm=LLMConfig(model_name="text-generation/nano", default_parameter=LLMParameter(temperature=1.0)),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
