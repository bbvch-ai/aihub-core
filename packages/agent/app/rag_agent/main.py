# ruff: noqa: E402
from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from swiss_ai_hub.core.infrastructure import AIHubSettings, enable_logging

from app.rag_agent.templates import get_all_templates
from swiss_ai_hub.agent.agents.rag_agent import RAGAgent, RAGAgentConfig
from swiss_ai_hub.agent.runners import AgentRunner

enable_logging()


async def main():
    runner = AgentRunner(
        agent_type=RAGAgent,
        agent_config=RAGAgentConfig.as_form(),
        templates=get_all_templates(),
    )

    await runner.run_forever()


if __name__ == "__main__":
    print(AIHubSettings().startup_banner)
    asyncio.run(main())
