from aihub_agent.agents.abstract.Agent import Agent
from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import StartEvent, StopEvent


class DisplayingAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent, displayer: EventDisplayer) -> StopEvent:
        print("[DisplayingAgent.start_step]", event)
        await displayer.display_thought("Let me think....")
        await displayer.display_chunk("This is some chunk that is sent to the user", model_name="gpt-4")
        return StopEvent()
