# ruff: noqa: E402
from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from swiss_ai_hub.core.infrastructure import AIHubSettings, enable_logging

from swiss_ai_hub.agent.agents.expert_asking_agent.expert_asking_agent import ExpertAskingAgent
from swiss_ai_hub.agent.agents.expert_asking_agent.expert_asking_agent_config import ExpertAskingAgentConfig
from swiss_ai_hub.agent.runners.agent_runner import AgentRunner

enable_logging()


async def main():
    runner = AgentRunner(
        agent_type=ExpertAskingAgent,
        agent_config=ExpertAskingAgentConfig.as_form(),
    )

    await runner.run_forever()


if __name__ == "__main__":
    print(AIHubSettings().startup_banner)
    asyncio.run(main())
