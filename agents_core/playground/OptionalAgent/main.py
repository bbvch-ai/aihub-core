import asyncio
import logging
from asyncio import sleep

from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from agents_core.runners.AgentRunner import AgentRunner
from lib_core.i18n.LocaleString import LocaleString
from lib_core.nats.events import StartEvent
from playground.OptionalAgent.OptionalAgent import OptionalAgent
from playground.OptionalAgent.OptionalAgentConfig import OptionalAgentConfig

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(name)s.%(funcName)s] %(levelname)s: %(message)s'
)
logging.getLogger().setLevel(logging.DEBUG)

async def main():
    runner = AgentRunner(
        servers=["nats://localhost:4222"],
        agent_class=OptionalAgent,
        agent_config=OptionalAgentConfig(
            agent_id="optional_agent",
            name=LocaleString(en="Optional Agent"),
            description=LocaleString(en="This is an agent with optional input"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )
    await runner.start()
    await runner.send_event(
        start_event=StartEvent(messages=[]),
        thread_id=str(ObjectId()),
        display_id=str(ObjectId()),
        run_id=str(ObjectId()),
    )
    await sleep(5)
    await runner.stop()

if __name__ == "__main__":
    asyncio.run(main())