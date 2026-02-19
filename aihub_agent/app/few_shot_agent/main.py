# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from aihub_lib.infrastructure.logging.logger import enable_logging

from aihub_agent.agents.FewShotAgent.FewShotAgent import FewShotAgent
from aihub_agent.agents.FewShotAgent.FewShotAgentConfig import FewShotAgentConfig
from aihub_agent.runners.AgentRunner import AgentRunner
from app.few_shot_agent.templates import ALL_TEMPLATES

enable_logging()


async def main():
    runner = AgentRunner(
        agent_type=FewShotAgent,
        agent_config=FewShotAgentConfig.as_form(),
        templates=ALL_TEMPLATES,
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
