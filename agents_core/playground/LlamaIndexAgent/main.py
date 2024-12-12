import asyncio
import logging
from asyncio import sleep

from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from agents_core.runners.AgentRunner import AgentRunner
from agents_core.runners.AgentTestRunner import AgentTestRunner
from lib_core.generative_ai.llms.models.chat.azure.AzureOpenAILLMConfig import AzureOpenAILLMConfig, \
    AzureOpenAIParameter
from lib_core.i18n.LocaleString import LocaleString
from lib_core.nats.events import StartEvent
from playground.LlamaIndexAgent.LlamaIndexAgent import LlamaIndexAgent
from playground.LlamaIndexAgent.LlamaIndexAgentConfig import LlamaIndexAgentConfig


async def main():
    runner = AgentTestRunner(
        agent_type=LlamaIndexAgent,
        agent_config=LlamaIndexAgentConfig(
            agent_id="llama_index_agent",
            name=LocaleString(en="Llama Index Agent"),
            description=LocaleString(en="This is an agent that uses a llama index llm"),
            system_prompt=LocaleString(en="You are an agent"),
            llm=AzureOpenAILLMConfig(
                name="gpt-4o",
                api_endpoint="https://aihub-dev-openai-che.openai.azure.com/",
                api_version="2023-12-01-preview",
                prompt_tokens_costs_per_thousand=0.0045,
                completion_tokens_costs_per_thousand=0.0133,
                default_parameter=AzureOpenAIParameter(temperature=0.0)
            )
        ),
    )

    async with runner.test_run(delay_before_stop=5) as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=StartEvent(messages=[ChatMessage(content="Hey!", role=MessageRole.USER)])
        )

if __name__ == "__main__":
    asyncio.run(main())