# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from aihub_lib.infrastructure.logging.logger import enable_logging

from aihub_agent.agents.NamespaceSelectionAgent import NamespaceSelectionAgent
from aihub_agent.agents.NamespaceSelectionAgent.configs import NamespaceSelectionAgentConfig
from aihub_agent.runners.AgentRunner import AgentRunner

enable_logging()


async def main():
    runner = AgentRunner(
        agent_type=NamespaceSelectionAgent,
        agent_config=NamespaceSelectionAgentConfig.as_form(),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
