import asyncio

from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events import UserMessageEvent
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
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
            agent_class=LlamaIndexAgent.__name__,
            name=LocaleString(en="Llama Index Agent"),
            description=LocaleString(en="This is an agent that uses a llama index llm"),
            llm=LLMConfig(model_name="text-generation/gpt-oss-120b"),
        ),
    )

    async with runner.test_run(delay_before_stop=5) as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content="Hey!", role=MessageRole.USER)],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
