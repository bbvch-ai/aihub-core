from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import StartEvent, StopEvent
from playground.minimal_workflow.configured_workflow.ConfiguredAgentConfig import (
    StartStepConfig,
    ConfiguredAgentConfig,
)
from playground.minimal_workflow.configured_workflow.events.EventA import EventA
from playground.minimal_workflow.configured_workflow.events.EventB import EventB


class ConfiguredAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent, start_config: StartStepConfig) -> EventA:
        print(f"[ConfiguredAgent.start_step] Step config value: '{start_config.some_step_value}'")
        return EventA(payload=start_config.some_step_value)

    @step()
    async def middle_step(self, event: EventA, agent_config: ConfiguredAgentConfig) -> EventB:
        print(f"[ConfiguredAgent.middle_step] Agent config value: '{agent_config.some_agent_value}'")
        return EventB(payload=agent_config.some_agent_value)

    @step()
    async def end_step(self, event: EventB) -> StopEvent:
        return StopEvent()
