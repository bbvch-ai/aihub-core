from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio  # noqa: E402

from llama_index.core.base.llms.types import ChatMessage, MessageRole  # noqa: E402
from swiss_ai_hub.core.events.agent import UserMessageEvent  # noqa: E402
from swiss_ai_hub.core.generative_ai import LLMConfig  # noqa: E402
from swiss_ai_hub.core.i18n import LocaleString  # noqa: E402
from swiss_ai_hub.core.infrastructure import enable_logging  # noqa: E402
from swiss_ai_hub.core.testing.auth_utils import fake_user  # noqa: E402

from playground.minimal_workflow.llama_index_workflow.llama_index_agent import (  # noqa: E402
    LlamaIndexAgent,
)
from playground.minimal_workflow.llama_index_workflow.llama_index_agent_config import (  # noqa: E402
    LlamaIndexAgentConfig,
)
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner  # noqa: E402

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=LlamaIndexAgent,
        agent_config=LlamaIndexAgentConfig(
            agent_id="llama_index_agent",
            agent_class=LlamaIndexAgent.__name__,
            name=LocaleString(en="Llama Index Agent"),
            description=LocaleString(en="This is an agent that uses a llama index llm"),
            llm=LLMConfig(model_name="text-generation/Qwen3-VL-235B-A22B-Instruct"),
        ),
    )

    async with runner.test_run(delay_before_stop=5) as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content="Hey!", role=MessageRole.USER)],
                user=fake_user(),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
