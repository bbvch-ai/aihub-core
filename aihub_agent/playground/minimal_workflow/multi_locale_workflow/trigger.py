import asyncio
import os

from llama_index.core.base.llms.types import ChatMessage, MessageRole

from aihub_agent.runners.AgentTestRunner import AgentTestRunner
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent
from playground.minimal_workflow.multi_locale_workflow.MultiLocaleAgent import MultiLocaleAgent
from playground.minimal_workflow.multi_locale_workflow.MultiLocaleAgentConfig import MultiLocaleAgentConfig


async def main():
    runner = AgentTestRunner(
        agent_type=MultiLocaleAgent,
        agent_config=MultiLocaleAgentConfig(
            agent_id="multi_locale_agent",
            name=LocaleString(en="Multi Locale Agent"),
            description=LocaleString(
                en="This is an agent that knows multiple languages"
            ),
            system_prompt=LocaleString(en="You are an agent"),
        ),
        locale_paths=[
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "translations")
        ],
    )

    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            start_event=StartEvent(
                locale="en",
                messages=[ChatMessage(content="Hello", role=MessageRole.USER)],
            ),
            topic=topic,
        )


if __name__ == "__main__":
    asyncio.run(main())
