import asyncio

from aihub_lib.auth.dependencies.DangerousDevelopmentOnlyAuthHandler.DangerousDevelopmentOnlyAuthSettings import (
    DangerousDevelopmentOnlyAuthSettings,
)
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.logging.logger import enable_logging
from aihub_lib.nats.events import UserMessageEvent
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from playground.minimal_workflow.simple_workflow.SimpleAgent import SimpleAgent
from playground.minimal_workflow.simple_workflow.SimpleAgentConfig import (
    SimpleAgentConfig,
)

enable_logging()


async def main():
    runner = AgentTestRunner(
        agent_type=SimpleAgent,
        agent_config=SimpleAgentConfig(
            agent_id="simple_agent",
            agent_class=SimpleAgent.__name__,
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
