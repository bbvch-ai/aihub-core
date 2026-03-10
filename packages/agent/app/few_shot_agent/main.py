# ruff: noqa: E402
from swiss_ai_hub.core.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from swiss_ai_hub.core.infrastructure.api.AIHubSettings import AIHubSettings
from swiss_ai_hub.core.infrastructure.logging.logger import enable_logging

from app.few_shot_agent.templates import ALL_TEMPLATES
from swiss_ai_hub.agent.agents.FewShotAgent.FewShotAgent import FewShotAgent
from swiss_ai_hub.agent.agents.FewShotAgent.FewShotAgentConfig import FewShotAgentConfig
from swiss_ai_hub.agent.runners.AgentRunner import AgentRunner

enable_logging()


async def main():
    runner = AgentRunner(
        agent_type=FewShotAgent,
        agent_config=FewShotAgentConfig.as_form(),
        templates=ALL_TEMPLATES,
    )

    await runner.run_forever()


if __name__ == "__main__":
    print(AIHubSettings().startup_banner)
    asyncio.run(main())
