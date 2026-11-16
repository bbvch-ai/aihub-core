# ruff: noqa: E402
from swiss_ai_hub.core.infrastructure import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from swiss_ai_hub.agent import AgentRunner
from swiss_ai_hub.core.infrastructure import AIHubSettings, enable_logging

from app.email_classification_agent.templates import get_all_templates
from swiss_ai_hub.ee.agents.email_classification_agent import (
    EmailClassificationAgent,
    EmailClassificationAgentConfig,
)

enable_logging()


async def main():
    runner = AgentRunner(
        agent_type=EmailClassificationAgent,
        agent_config=EmailClassificationAgentConfig.as_form(),
        templates=get_all_templates(),
    )

    await runner.run_forever()


if __name__ == "__main__":
    print(AIHubSettings().startup_banner)
    asyncio.run(main())
