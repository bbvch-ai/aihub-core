import asyncio
import logging
import os

from llama_index.core.base.llms.types import ChatMessage, MessageRole

from agents_core.runners.AgentTestRunner import AgentTestRunner
from lib_core.i18n.LocaleString import LocaleString
from lib_core.nats.events import StartEvent
from playground.MultiLocaleAgent.MultiLocaleAgent import MultiLocaleAgent
from playground.MultiLocaleAgent.MultiLocaleAgentConfig import MultiLocaleAgentConfig

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(name)s.%(funcName)s] %(levelname)s: %(message)s'
)
logging.getLogger().setLevel(logging.DEBUG)

async def main():
    runner = AgentTestRunner(
        agent_class=MultiLocaleAgent,
        agent_config=MultiLocaleAgentConfig(
            agent_id="multi_locale_agent",
            name=LocaleString(en="Multi Locale Agent"),
            description=LocaleString(en="This is an agent that knows multiple languages"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
        locale_paths=[
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "translations")
        ]
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