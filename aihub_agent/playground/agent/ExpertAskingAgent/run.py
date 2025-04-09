import asyncio

from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgent import ExpertAskingAgent
from aihub_agent.agents.ExpertAskingAgent.ExpertAskingAgentConfig import ExpertAskingAgentConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
    AzureOpenAIParameter,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.testing.logging.logger import enable_logging

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=ExpertAskingAgent,
        agent_config=ExpertAskingAgentConfig(
            agent_id="expert_agent",
            name=LocaleString(en="Expert Asking Agent"),
            description=LocaleString(en="This is an agent that can be used to develop the frontend"),
            system_prompt=LocaleString(en="You are an agent"),
            conversation_id="B08D8FP20TZ:T08AZPNJV33:C08MK7Z8GU9",
            open_webui_knowledge_id="19f27af1-ab04-494f-877c-2f3e5fb24e52",
            open_webui_api_key="sk-95736c105e1d48119a48f4f38716550c",
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
