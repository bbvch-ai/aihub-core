# ruff: noqa: E402
from swiss_ai_hub.core.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from swiss_ai_hub.core.infrastructure.api.AIHubSettings import AIHubSettings
from swiss_ai_hub.core.infrastructure.logging.logger import enable_logging

from swiss_ai_hub.agent.agents.ExpertRagAgent.configs.ExpertRAGAgentConfig import ExpertRAGAgentConfig
from swiss_ai_hub.agent.agents.ExpertRagAgent.ExpertRAGAgent import ExpertRAGAgent
from swiss_ai_hub.agent.runners.AgentRunner import AgentRunner

enable_logging()


async def main():
    runner = AgentRunner(
        agent_type=ExpertRAGAgent,
        agent_config=ExpertRAGAgentConfig.as_form(),
    )

    await runner.run_forever()


if __name__ == "__main__":
    print(AIHubSettings().startup_banner)
    asyncio.run(main())
