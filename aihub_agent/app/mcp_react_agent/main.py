# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from aihub_lib.infrastructure.api.AIHubSettings import AIHubSettings
from aihub_lib.infrastructure.logging.logger import enable_logging

from aihub_agent.agents.McpReactAgent.configs.McpReactAgentConfig import McpReactAgentConfig
from aihub_agent.agents.McpReactAgent.McpReactAgent import McpReactAgent
from aihub_agent.runners.AgentRunner import AgentRunner

enable_logging()


async def main():
    runner = AgentRunner(
        agent_type=McpReactAgent,
        agent_config=McpReactAgentConfig.as_form(),
    )

    await runner.run_forever()


if __name__ == "__main__":
    print(AIHubSettings().startup_banner)
    asyncio.run(main())
