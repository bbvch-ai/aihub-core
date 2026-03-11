# ruff: noqa: E402
from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from swiss_ai_hub.core.infrastructure import AIHubSettings, enable_logging

from swiss_ai_hub.agent.agents.namespace_selection_agent import NamespaceSelectionAgent
from swiss_ai_hub.agent.agents.namespace_selection_agent.configs import NamespaceSelectionAgentConfig
from swiss_ai_hub.agent.runners.agent_runner import AgentRunner

enable_logging()


async def main():
    runner = AgentRunner(
        agent_type=NamespaceSelectionAgent,
        agent_config=NamespaceSelectionAgentConfig.as_form(),
    )

    await runner.run_forever()


if __name__ == "__main__":
    print(AIHubSettings().startup_banner)
    asyncio.run(main())
