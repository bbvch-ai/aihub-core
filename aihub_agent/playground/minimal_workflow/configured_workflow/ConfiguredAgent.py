from aihub_lib.nats.events import StartEvent, StopEvent

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.configured_workflow.ConfiguredAgentConfig import (
    StartStepConfig,
    ConfiguredAgentConfig,
)
from playground.minimal_workflow.configured_workflow.events.EventConfiguredA import EventConfiguredA
from playground.minimal_workflow.configured_workflow.events.EventConfiguredB import EventConfiguredB


class ConfiguredAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent, start_config: StartStepConfig) -> EventConfiguredA:
        print(f"[ConfiguredAgent.start_step] Step config value: '{start_config.some_step_value}'")
        return EventConfiguredA(payload=start_config.some_step_value)

    @step()
    async def middle_step(self, event: EventConfiguredA, agent_config: ConfiguredAgentConfig) -> EventConfiguredB:
        print(f"[ConfiguredAgent.middle_step] Agent config value: '{agent_config.some_agent_value}'")
        return EventConfiguredB(payload=agent_config.some_agent_value)

    @step()
    async def end_step(self, event: EventConfiguredB) -> StopEvent:
        return StopEvent()
