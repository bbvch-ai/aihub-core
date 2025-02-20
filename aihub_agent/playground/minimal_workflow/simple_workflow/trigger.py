import asyncio

from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent, UserMessageEvent
from aihub_lib.testing.auth_utils.fake_user import fake_user
from aihub_lib.testing.logging.logger import enable_logging
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
            name=LocaleString(en="Simple Agent"),
            description=LocaleString(en="This is a very simple agent"),
            system_prompt=LocaleString(en="You are an agent"),
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
