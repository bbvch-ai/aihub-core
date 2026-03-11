# ruff: noqa: E402
from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from swiss_ai_hub.core.infrastructure import AIHubSettings, enable_logging

from app.llm_wrapping_agent.templates import ALL_TEMPLATES
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent import LLMWrappingAgent
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent_config import LLMWrappingAgentConfig
from swiss_ai_hub.agent.runners.agent_runner import AgentRunner

enable_logging()


async def main():
    runner = AgentRunner(
        agent_type=LLMWrappingAgent,
        agent_config=LLMWrappingAgentConfig.as_form(),
        templates=ALL_TEMPLATES,
    )

    await runner.run_forever()


if __name__ == "__main__":
    print(AIHubSettings().startup_banner)
    asyncio.run(main())
