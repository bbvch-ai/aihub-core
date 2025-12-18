# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging

from aihub_agent.agents.HitlDemoAgent import HitlDemoAgent, HitlDemoAgentConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=HitlDemoAgent,
        default_agent_config=HitlDemoAgentConfig(
            agent_id="hitl_demo_agent",
            agent_class=HitlDemoAgent.__name__,
            name=LocaleString(en="HITL Demo Agent"),
            description=LocaleString(en="Demo agent showcasing all HITL types"),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
