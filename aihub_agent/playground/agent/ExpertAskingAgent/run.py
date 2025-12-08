# ruff: noqa: E402
from aihub_lib.infrastructure.opentelemetry.AihubInstrumentor import AihubInstrumentor  # isort: skip

AihubInstrumentor().instrument()

import asyncio

from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging

from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgent import ExpertAskingAgent
from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgentConfig import ExpertAskingAgentConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=ExpertAskingAgent,
        default_agent_config=ExpertAskingAgentConfig(
            agent_id="expert_agent",
            agent_class=ExpertAskingAgent.__name__,
            name=LocaleString(en="Expert Asking Agent"),
            description=LocaleString(en="This is an agent that can be used to develop the frontend"),
            slack_channel_id="C08MK7Z8GU9",
            open_webui_knowledge_id="c49fd8bb-8e6b-4ed5-ba31-5e97b55bcbe8",
            open_webui_api_key="sk-acb200cc04414a84867ad239471549cb",
            open_webui_api_url="http://localhost:8080",
            llm=LLMConfig(model_name="text-generation/mini"),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
