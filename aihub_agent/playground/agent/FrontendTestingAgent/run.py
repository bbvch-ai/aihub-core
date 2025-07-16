import asyncio

from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
    AzureOpenAIParameter,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.RedisConfig import RedisConfig
from aihub_lib.nats.NatsConfig import NatsConfig
from aihub_lib.testing.logging.logger import enable_logging

from aihub_agent.runners.MultiprocessAgentRunner import MultiprocessAgentRunner
from playground.agent.FrontendTestingAgent.FrontendTestingAgent import FrontendTestingAgent
from playground.agent.FrontendTestingAgent.FrontendTestingAgentConfig import FrontendTestingAgentConfig

enable_logging()


async def main():
    runner = MultiprocessAgentRunner(
        servers=[NatsConfig().NATS_ENDPOINT],
        redis_url=RedisConfig().REDIS_URL,
        agent_type=FrontendTestingAgent,
        agent_config=FrontendTestingAgentConfig(
            agent_id="frontend_testing",
            agent_class=FrontendTestingAgent.__name__,
            name=LocaleString(en="Frontend Testing Agent"),
            description=LocaleString(en="This is an agent that can be used to develop the frontend"),
            system_prompt=LocaleString(en="You are an agent"),
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
