import asyncio

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.generative_ai.llms.models.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
    AzureOpenAIParameter,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.testing.logging.logger import enable_logging
from playground.DevAgent.DevAgent import DevAgent
from playground.DevAgent.DevAgentConfig import DevAgentConfig

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=DevAgent,
        agent_config=DevAgentConfig(
            agent_id="dev_agent",
            name=LocaleString(en="Dev Agent"),
            description=LocaleString(
                en="This is an agent that can be used to develop the frontend"
            ),
            system_prompt=LocaleString(en="You are an agent"),
            llm=AzureOpenAILLMConfig(
                name="gpt-4o",
                api_endpoint="https://aihub-dev-openai-che.openai.azure.com/",
                api_version="2023-12-01-preview",
                prompt_tokens_costs_per_thousand=0.0045,
                completion_tokens_costs_per_thousand=0.0133,
                default_parameter=AzureOpenAIParameter(temperature=0.0),
            ),
        ),
    )

    await runner.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
