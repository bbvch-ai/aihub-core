from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import StartEvent, StopEvent
from playground.SimpleAgent.Events.EventA import EventA


class SimpleAgent(Agent):

    @step()
    async def start_step(self, event: StartEvent) -> EventA:
        print("[SimpleAgent.start_step]", event)
        return EventA(payload=event.messages[-1].content)

    @step()
    async def end_step(self, event: EventA) -> StopEvent:
        print("[SimpleAgent.end_step]", event)
        return StopEvent()