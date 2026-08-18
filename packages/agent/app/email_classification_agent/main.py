# ruff: noqa: E402
from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from swiss_ai_hub.core.infrastructure import AIHubSettings, enable_logging

from swiss_ai_hub.agent.agents.email_classification_agent import (
    EmailClassificationAgent,
    EmailClassificationAgentConfig,
)
from swiss_ai_hub.agent.runners import AgentRunner

enable_logging()


async def main():
    runner = AgentRunner(
        agent_type=EmailClassificationAgent,
        agent_config=EmailClassificationAgentConfig.as_form(),
    )

    await runner.run_forever()


if __name__ == "__main__":
    print(AIHubSettings().startup_banner)
    asyncio.run(main())
