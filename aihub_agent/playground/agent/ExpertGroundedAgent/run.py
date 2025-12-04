# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging

from aihub_agent.agents.ExpertGroundedAgent.ExpertGroundedAgent import ExpertGroundedAgent
from aihub_agent.agents.ExpertGroundedAgent.ExpertGroundedAgentConfig import ExpertGroundedAgentConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=ExpertGroundedAgent,
        default_agent_config=ExpertGroundedAgentConfig(
            agent_id="grounded_agent",
            agent_class=ExpertGroundedAgent.__name__,
            name=LocaleString(en="Grounded Agent"),
            description=LocaleString(en="This is an agent that can be used to develop the frontend"),
            expert_asking_agent_class="ExpertAskingAgent",
            expert_asking_agent_id="expert_agent",
            llm=LLMConfig(model_name="text-generation/mini"),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
