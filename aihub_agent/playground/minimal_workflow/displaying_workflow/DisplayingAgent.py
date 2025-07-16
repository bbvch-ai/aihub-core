from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.nats.events import StartEvent, StopEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.displaying_workflow.DisplayingAgentConfig import DisplayingAgentConfig


class DisplayingAgent(Agent):
    agent_config_type: type[DisplayingAgentConfig] = DisplayingAgentConfig

    @step()
    async def start_step(self, event: StartEvent, displayer: EventDisplayer) -> StopEvent:
        print("[DisplayingAgent.start_step]", event)
        await displayer.display_thought("Let me think....")
        await displayer.display_chunk("This is some chunk that is sent to the user", model_name="gpt-4")
        return StopEvent()
