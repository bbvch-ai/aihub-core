import asyncio

from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.generative_ai.llms.models.chat.self_hosted.SelfHostedLLMConfig import (
    SelfHostedLLMConfig,
    SelfHostedLLMParameter,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent
from aihub_lib.testing.logging.logger import enable_logging
from playground.minimal_workflow.llama_index_workflow.LlamaIndexAgent import (
    LlamaIndexAgent,
)
from playground.minimal_workflow.llama_index_workflow.LlamaIndexAgentConfig import (
    LlamaIndexAgentConfig,
)

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=LlamaIndexAgent,
        agent_config=LlamaIndexAgentConfig(
            agent_id="llama_index_agent",
            name=LocaleString(en="Llama Index Agent"),
            description=LocaleString(en="This is an agent that uses a llama index llm"),
            system_prompt=LocaleString(en="You are an agent"),
            llm=SelfHostedLLMConfig(
                name="unsloth/Llama-3.2-1B-Instruct",
                base_url="http://localhost:8182/v1",
                api_key=None,
                context_size=512,
                is_chat_model=True,
                is_function_calling_model=False,
                default_parameter=SelfHostedLLMParameter(
                    logit_bias=None,
                    logprobs=None,
                ),
            ),
        ),
    )

    async with runner.test_run(delay_before_stop=5) as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=StartEvent(messages=[ChatMessage(content="Hey!", role=MessageRole.USER)]),
        )


if __name__ == "__main__":
    asyncio.run(main())
