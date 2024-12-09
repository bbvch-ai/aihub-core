from agents_core.agents.abstract.Agent import Agent
from agents_core.displayers.EventDisplayer import EventDisplayer
from agents_core.workflow.decorators.step import step
from lib_core.nats.events import StartEvent, StopEvent
from playground.SimpleAgent.Events.EventA import EventA


class DisplayingAgent(Agent):

    @step()
    async def start_step(self, event: StartEvent, displayer: EventDisplayer) -> StopEvent:
        print("[DisplayingAgent.start_step]", event)
        await displayer.display_thought("Let me think....")
        await displayer.display_chunk("This is some chunk that is sent to the user")
        return StopEvent()
