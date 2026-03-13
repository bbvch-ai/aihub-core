# ruff: noqa: E402
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip  # noqa: E402

AihubInstrumentor().instrument()

import asyncio  # noqa: E402

from swiss_ai_hub.core.i18n import LocaleString  # noqa: E402
from swiss_ai_hub.core.infrastructure import enable_logging  # noqa: E402

from playground.agent.hitl_demo_agent.hitl_demo_agent import HitlDemoAgent  # noqa: E402
from playground.agent.hitl_demo_agent.hitl_demo_agent_config import HitlDemoAgentConfig  # noqa: E402
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner  # noqa: E402

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
