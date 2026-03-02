# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from aihub_lib import swiss_ai_hub_ascii
from aihub_lib.infrastructure.logging.logger import enable_logging

from aihub_agent.agents.RetrievalAgent.configs.RetrievalAgentConfig import RetrievalAgentConfig
from aihub_agent.agents.RetrievalAgent.RetrievalAgent import RetrievalAgent
from aihub_agent.runners.AgentRunner import AgentRunner

enable_logging()
print(swiss_ai_hub_ascii("RetrievalAgent"))


async def main():
    runner = AgentRunner(
        agent_type=RetrievalAgent,
        agent_config=RetrievalAgentConfig.as_form(),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
