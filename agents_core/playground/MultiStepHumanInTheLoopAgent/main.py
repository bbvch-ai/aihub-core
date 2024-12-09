import asyncio
import logging
from asyncio import sleep

from bson import ObjectId

from agents_core.runners.AgentRunner import AgentRunner
from lib_core.i18n.LocaleString import LocaleString
from lib_core.nats.events import StartEvent
from lib_core.nats.topics.agents.PartialAgentTopic import PartialAgentTopic
from playground.MultiStepHumanInTheLoopAgent.Events.FirstStepHumanInTheLoop import FirstStepHumanInTheLoop
from playground.MultiStepHumanInTheLoopAgent.Events.SecondStepHumanInTheLoop import SecondStepHumanInTheLoop
from playground.MultiStepHumanInTheLoopAgent.HumanInTheLoopAgent import MultiStepHumanInTheLoopAgent
from playground.MultiStepHumanInTheLoopAgent.HumanInTheLoopAgentConfig import MultiStepHumanInTheLoopAgentConfig

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(name)s.%(funcName)s] %(levelname)s: %(message)s'
)
logging.getLogger().setLevel(logging.DEBUG)

async def main():
    runner = AgentRunner(
        servers=["nats://localhost:4222"],
        agent_class=MultiStepHumanInTheLoopAgent,
        agent_config=MultiStepHumanInTheLoopAgentConfig(
            agent_id="multi_step_human_in_the_loop_agent",
            name=LocaleString(en="Multi Step Human in the Loop Agent"),
            description=LocaleString(en="This is an agent with the Human in the Loop over multiple steps"),
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
    first_request_event = FirstStepHumanInTheLoop.request(question="Shall I continue?", topic=PartialAgentTopic())
    await runner.send_event(
        start_event=FirstStepHumanInTheLoop.response(response="Yes, Please!", request_event=first_request_event),
        thread_id=thread_id,
        display_id=display_id,
        run_id=run_id,
    )
    await sleep(5)

    # Note: We 'fake' the request event here. This would normally be provided by the web client
    second_request_event = SecondStepHumanInTheLoop.request(question="Are you sure?", topic=PartialAgentTopic())
    await runner.send_event(
        start_event=SecondStepHumanInTheLoop.response(response="Yeees, absolutely!", request_event=second_request_event),
        thread_id=thread_id,
        display_id=display_id,
        run_id=run_id,
    )
    await sleep(5)

    await runner.stop()

if __name__ == "__main__":
    asyncio.run(main())