import asyncio

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.infrastructure.logging.logger import enable_logging
from swiss_ai_hub.core.nats.events import UserMessageEvent

from playground.minimal_workflow.simple_workflow.SimpleAgent import SimpleAgent
from playground.minimal_workflow.simple_workflow.SimpleAgentConfig import (
    SimpleAgentConfig,
)
from swiss_ai_hub.agent.runners.AgentTestRunner import AgentTestRunner

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=SimpleAgent,
        agent_config=SimpleAgentConfig(
            agent_id="simple_agent",
            name=LocaleString(en="Simple Agent"),
            description=LocaleString(en="This is a very simple agent"),
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
