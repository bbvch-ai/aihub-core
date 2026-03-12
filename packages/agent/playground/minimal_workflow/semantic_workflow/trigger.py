from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

import asyncio

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.auth import DangerousDevelopmentOnlyAuthSettings
from swiss_ai_hub.core.events.agent import UserMessageEvent
from swiss_ai_hub.core.i18n import LocaleString

from playground.minimal_workflow.semantic_workflow.semantic_event_agent import (
    SemanticEventAgent,
)
from playground.minimal_workflow.semantic_workflow.semantic_event_agent_config import (
    SemanticEventAgentConfig,
)
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner


async def main():
    runner = AgentTestRunner(
        agent_type=SemanticEventAgent,
        agent_config=SemanticEventAgentConfig(
            agent_id="semantic_event_agent",
            name=LocaleString(en="Semantic Event Agent"),
            description=LocaleString(en="This is an agent with semantic events"),
        ),
    )

    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            topic=topic,
            start_event=UserMessageEvent(
                messages=[ChatMessage(content="Hello", role=MessageRole.USER)],
                user=DangerousDevelopmentOnlyAuthSettings().get_user_identity(),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
