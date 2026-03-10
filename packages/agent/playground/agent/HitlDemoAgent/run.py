# ruff: noqa: E402
from swiss_ai_hub.core.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.infrastructure.logging.logger import enable_logging

from playground.agent.HitlDemoAgent.HitlDemoAgent import HitlDemoAgent
from playground.agent.HitlDemoAgent.HitlDemoAgentConfig import HitlDemoAgentConfig
from swiss_ai_hub.agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=HitlDemoAgent,
        agent_config=HitlDemoAgentConfig(
            agent_id="hitl_demo_agent",
            agent_class=HitlDemoAgent.__name__,
            name=LocaleString(en="HITL Demo Agent"),
            description=LocaleString(en="Demo agent showcasing all HITL types"),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
