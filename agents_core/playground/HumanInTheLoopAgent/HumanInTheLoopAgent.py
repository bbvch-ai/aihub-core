from agents_core.agents.abstract.Agent import Agent
from agents_core.workflow.decorators.step import step
from lib_core.nats.events import StartEvent, StopEvent
from lib_core.nats.events.human_in_the_loop import HumanInTheLoop


class HumanInTheLoopAgent(Agent):

    @step()
    async def start_step(self, event: StartEvent) -> HumanInTheLoop.request:
        print("[HumanInTheLoopAgent.start_step]")
        return HumanInTheLoop.invoke(question="Shall I continue?")

    @step()
    async def end_step(self, event: HumanInTheLoop.response) -> StopEvent:
        print("[HumanInTheLoopAgent.end_step]", event.request_event.question, event.response)
        return StopEvent()