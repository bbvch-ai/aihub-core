# ruff: noqa: E402
from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from swiss_ai_hub.core.infrastructure import AIHubSettings, enable_logging

from swiss_ai_hub.agent.agents.universal_agent import UniversalAgent, UniversalAgentConfig
from swiss_ai_hub.agent.runners import AgentRunner

enable_logging()


async def main():
    await AgentRunner(agent_type=UniversalAgent, agent_config=UniversalAgentConfig.as_form()).run_forever()


if __name__ == "__main__":
    print(AIHubSettings().startup_banner)
    asyncio.run(main())
