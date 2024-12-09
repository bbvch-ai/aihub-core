import asyncio
import logging
from asyncio import sleep

from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from agents_core.runners.AgentRunner import AgentRunner
from lib_core.i18n.LocaleString import LocaleString
from lib_core.nats.events import StartEvent
from playground.FanOutAgent.FanOutAgent import FanOutAgent
from playground.FanOutAgent.FanOutAgentConfig import FanOutAgentConfig

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(name)s.%(funcName)s] %(levelname)s: %(message)s'
)
logging.getLogger().setLevel(logging.DEBUG)

async def main():
    runner = AgentRunner(
        servers=["nats://localhost:4222"],
        agent_class=FanOutAgent,
        agent_config=FanOutAgentConfig(
            agent_id="fan_out_agent",
            name=LocaleString(en="Fan Out Agent"),
            description=LocaleString(en="This is an agent that fans out multiple steps"),
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