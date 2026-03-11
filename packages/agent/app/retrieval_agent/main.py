# ruff: noqa: E402
from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from swiss_ai_hub.core.infrastructure import AIHubSettings, enable_logging

from swiss_ai_hub.agent.agents.retrieval_agent.configs.retrieval_agent_config import RetrievalAgentConfig
from swiss_ai_hub.agent.agents.retrieval_agent.retrieval_agent import RetrievalAgent
from swiss_ai_hub.agent.runners.agent_runner import AgentRunner

enable_logging()


async def main():
    runner = AgentRunner(
        agent_type=RetrievalAgent,
        agent_config=RetrievalAgentConfig.as_form(),
    )

    await runner.run_forever()


if __name__ == "__main__":
    print(AIHubSettings().startup_banner)
    asyncio.run(main())
