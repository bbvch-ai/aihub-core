import asyncio
import logging
from asyncio import sleep

from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from agents_core.runners.AgentRunner import AgentRunner
from lib_core.i18n.LocaleString import LocaleString
from lib_core.nats.events import StartEvent
from playground.DisplayingAgent.DisplayingAgent import DisplayingAgent
from playground.DisplayingAgent.DisplayingAgentConfig import DisplayingAgentConfig
from playground.SimpleAgent.SimpleAgent import SimpleAgent
from playground.SimpleAgent.SimpleAgentConfig import SimpleAgentConfig

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(name)s.%(funcName)s] %(levelname)s: %(message)s'
)
logging.getLogger().setLevel(logging.DEBUG)

async def main():
    runner = AgentRunner(
        servers=["nats://localhost:4222"],
        agent_class=DisplayingAgent,
        agent_config=DisplayingAgentConfig(
            agent_id="displaying_agent",
            name=LocaleString(en="Displaying Agent"),
            description=LocaleString(en="This is a very simple agent that displays stuff to the user"),
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