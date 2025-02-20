import asyncio

from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.agents.basic.LLMWrappingAgent.LLMWrappingAgent import LLMWrappingAgent
from aihub_agent.agents.basic.LLMWrappingAgent.LLMWrappingAgentConfig import (
    LLMWrappingAgentConfig,
)
from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.generative_ai.resources.models.llm.chat.azure.AzureOpenAILLMConfig import (
    AzureOpenAILLMConfig,
    AzureOpenAIParameter,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import UserMessageEvent
from aihub_lib.testing.auth_utils.fake_user import fake_user
from aihub_lib.testing.logging.logger import enable_logging

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=LLMWrappingAgent,
        agent_config=LLMWrappingAgentConfig(
            agent_id="dev_agent",
            name=LocaleString(en="Dev Agent"),
            description=LocaleString(en="This is an agent that can be used to develop the frontend"),
            system_prompt=LocaleString(en="You are an agent"),
            llm=AzureOpenAILLMConfig(
                name="gpt-4o",
                base_url="https://aihub-dev-openai-che.openai.azure.com/",
                api_version="2023-12-01-preview",
                prompt_tokens_costs_per_thousand=0.0045,
                completion_tokens_costs_per_thousand=0.0133,
                default_parameter=AzureOpenAIParameter(temperature=0.0),
            ),
        ),
    )

    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content="Hello", role=MessageRole.USER)], user=fake_user()
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
