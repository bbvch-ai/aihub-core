import asyncio
import logging
from asyncio import sleep

from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage, MessageRole

from agents_core.runners.AgentRunner import AgentRunner
from lib_core.i18n.LocaleString import LocaleString
from lib_core.nats.events import StartEvent
from lib_core.nats.subscribers.NCSubscriber import NCSubscriber
from lib_core.nats.topic_managers.agents.AgentThreadTopicManager import AgentThreadTopicManager
from playground.SimpleAgent.SimpleAgent import SimpleAgent
from playground.SimpleAgent.SimpleAgentConfig import SimpleAgentConfig

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(name)s.%(funcName)s] %(levelname)s: %(message)s'
)
logging.getLogger().setLevel(logging.DEBUG)

async def main():
    events = []
    async def append_event(event, topic):
        events.append(event)

    runner = AgentRunner(
        servers=["nats://localhost:4222"],
        agent_class=SimpleAgent,
        agent_config=SimpleAgentConfig(
            agent_id="simple_agent",
            name=LocaleString(en="Simple Agent"),
            description=LocaleString(en="This is a very simple agent"),
            system_prompt=LocaleString(en="You are an agent"),
        ),
    )

    await runner.start()

    thread_id = str(ObjectId())
    display_id = str(ObjectId())
    run_id = str(ObjectId())

    event_subscriber = NCSubscriber.for_thread_control_events(
        nc=runner.nc,
        topic_manager=AgentThreadTopicManager.from_agent_instance_topic_manager(
            runner.topic_manager,
            thread_id=thread_id,
            display_id=display_id,
            run_id=run_id,
        ),
        handler=append_event,
    )
    await event_subscriber.start()

    await runner.send_event(
        start_event=StartEvent(messages=[ChatMessage(content="Hello", role=MessageRole.USER)]),
        thread_id=thread_id,
        display_id=display_id,
        run_id=run_id,
    )
    await sleep(5)
    await runner.stop()

    print(events)

if __name__ == "__main__":
    asyncio.run(main())