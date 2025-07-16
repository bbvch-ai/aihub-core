import asyncio

from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
    AzureOpenAIParameter,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.testing.logging.logger import enable_logging

from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgent import ExpertAskingAgent
from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgentConfig import ExpertAskingAgentConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=ExpertAskingAgent,
        agent_config=ExpertAskingAgentConfig(
            agent_id="expert_agent",
            agent_class=ExpertAskingAgent.__name__,
            name=LocaleString(en="Expert Asking Agent"),
            description=LocaleString(en="This is an agent that can be used to develop the frontend"),
            system_prompt=LocaleString(en="You are an agent"),
            slack_channel_id="C08MK7Z8GU9",
            open_webui_knowledge_id="c49fd8bb-8e6b-4ed5-ba31-5e97b55bcbe8",
            open_webui_api_key="sk-acb200cc04414a84867ad239471549cb",
            open_webui_api_url="http://localhost:8080",
            llm=AzureOpenAILLMConfig(
                name="gpt-4o",
                base_url="https://aihub-dev-openai-che.openai.azure.com/",
                api_version="2024-12-01-preview",
                prompt_tokens_costs_per_thousand=0.0045,
                completion_tokens_costs_per_thousand=0.0133,
                default_parameter=AzureOpenAIParameter(temperature=0.0),
            ),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
