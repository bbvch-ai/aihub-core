import asyncio
import logging

from llama_index.core.base.llms.types import ChatMessage, MessageRole

from agents_core.runners.AgentTestRunner import AgentTestRunner
from lib_core.i18n.LocaleString import LocaleString
from lib_core.nats.events import StartEvent
from playground.SimpleAgent.Events.EventA import EventA
from playground.SimpleAgent.SimpleAgent import SimpleAgent
from playground.SimpleAgent.SimpleAgentConfig import SimpleAgentConfig

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(name)s.%(funcName)s] %(levelname)s: %(message)s'
)
logging.getLogger().setLevel(logging.DEBUG)

async def main():
    runner = AgentTestRunner(
        agent_class=SimpleAgent,
        agent_config=SimpleAgentConfig(
            agent_id="simple_agent",
            name=LocaleString(en="Simple Agent"),
            description=LocaleString(en="This is a very simple agent"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )

    async with runner.test_run() as topic:
        await runner.send_event_from_topic(
            start_event=StartEvent(messages=[ChatMessage(content="Hello", role=MessageRole.USER)]),
            topic=topic,
        )

    assert runner.has_start_event, "Agent did not receive start event"
    assert runner.has_stop_event, "Agent did not receive stop event"
    assert runner.has_event_of_type(EventA), "Agent did not receive EventA"
    assert not runner.has_exception_event, "Agent received an exception event"
    assert runner.get_event_of_type(EventA).payload == "Hello", "Agent received incorrect data"


if __name__ == "__main__":
    asyncio.run(main())