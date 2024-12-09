import asyncio
import logging
from asyncio import sleep

from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from agents_core.runners.AgentRunner import AgentRunner
from lib_core.i18n.LocaleString import LocaleString
from lib_core.nats.events import StartEvent
from lib_core.nats.events.human_in_the_loop import HumanInTheLoop
from lib_core.nats.topics.agents.PartialAgentTopic import PartialAgentTopic
from playground.HumanInTheLoopAgent.HumanInTheLoopAgent import HumanInTheLoopAgent
from playground.HumanInTheLoopAgent.HumanInTheLoopAgentConfig import HumanInTheLoopAgentConfig
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
        agent_class=HumanInTheLoopAgent,
        agent_config=HumanInTheLoopAgentConfig(
            agent_id="human_in_the_loop_agent",
            name=LocaleString(en="Human in the Loop Agent"),
            description=LocaleString(en="This is an agent with the Human in the Loop"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )

    thread_id = str(ObjectId())
    display_id = str(ObjectId())
    run_id = str(ObjectId())

    await runner.start()
    await runner.send_event(
        start_event=StartEvent(messages=[]),
        thread_id=thread_id,
        display_id=display_id,
        run_id=run_id,
    )

    await sleep(5)

    # Note: We 'fake' the request event here. This would normally be provided by the web client
    request_event = HumanInTheLoop.request(question="Shall I continue?", topic=PartialAgentTopic())

    await runner.send_event(
        start_event=HumanInTheLoop.response(response="Yes, Please!", request_event=request_event),
        thread_id=thread_id,
        display_id=display_id,
        run_id=run_id,
    )
    await sleep(5)
    await runner.stop()

if __name__ == "__main__":
    asyncio.run(main())