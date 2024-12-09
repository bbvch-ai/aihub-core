import asyncio
import logging
from asyncio import sleep

from bson import ObjectId

from agents_core.runners.AgentRunner import AgentRunner
from lib_core.i18n.LocaleString import LocaleString
from playground.ContextAgent.ContextAgent import ContextAgent
from playground.ContextAgent.ContextAgentConfig import ContextAgentConfig
from playground.ContextAgent.Events.CustomStartEvent import CustomStartEvent

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(name)s.%(funcName)s] %(levelname)s: %(message)s'
)
logging.getLogger().setLevel(logging.DEBUG)

THREAD_ID = "6756ddb05c399b888009a559"

async def main():
    runner = AgentRunner(
        servers=["nats://localhost:4222"],
        agent_class=ContextAgent,
        agent_config=ContextAgentConfig(
            agent_id="context_agent",
            name=LocaleString(en="Context Agent"),
            description=LocaleString(en="This is an agent that accesses the run and thread context"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )
    await runner.start()
    await runner.send_event(
        start_event=CustomStartEvent(payload="This is some payload"),
        thread_id=THREAD_ID,
        display_id=str(ObjectId()),
        run_id=str(ObjectId()),
    )
    await sleep(5)
    await runner.stop()

if __name__ == "__main__":
    asyncio.run(main())