# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from aihub_lib import swiss_ai_hub_ascii
from aihub_lib.infrastructure.logging.logger import enable_logging

from aihub_agent.agents.RagAgent.configs.RAGAgentConfig import RAGAgentConfig
from aihub_agent.agents.RagAgent.RAGAgent import RAGAgent
from aihub_agent.runners.AgentRunner import AgentRunner

enable_logging()
print(swiss_ai_hub_ascii("RAGAgent"))


async def main():
    runner = AgentRunner(
        agent_type=RAGAgent,
        agent_config=RAGAgentConfig.as_form(),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
