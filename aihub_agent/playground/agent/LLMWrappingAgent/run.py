import asyncio

from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
    AzureOpenAIParameter,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.testing.logging.logger import enable_logging

from aihub_agent.agents.LLMWrappingAgent.LLMWrappingAgent import LLMWrappingAgent
from aihub_agent.agents.LLMWrappingAgent.LLMWrappingAgentConfig import LLMWrappingAgentConfig
from aihub_agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=LLMWrappingAgent,
        default_agent_config=LLMWrappingAgentConfig(
            agent_class=LLMWrappingAgent.__name__,
            agent_id="dev_agent",
            name=LocaleString(en="Dev Agent"),
            description=LocaleString(en="This is the default Dev Agent config"),
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
