from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import StartEvent, StopEvent
from playground.minimal_workflow.configured_workflow.ConfiguredAgentConfig import (
    StartStepConfig,
    ConfiguredAgentConfig,
)
from playground.minimal_workflow.configured_workflow.events.ConfiguredEventA import ConfiguredEventA
from playground.minimal_workflow.configured_workflow.events.ConfiguredEventB import ConfiguredEventB


class ConfiguredAgent(Agent):
    @step()
    async def start_step(self, event: StartEvent, start_config: StartStepConfig) -> ConfiguredEventA:
        print(f"[ConfiguredAgent.start_step] Step config value: '{start_config.some_step_value}'")
        return ConfiguredEventA(payload=start_config.some_step_value)

    @step()
    async def middle_step(self, event: ConfiguredEventA, agent_config: ConfiguredAgentConfig) -> ConfiguredEventB:
        print(f"[ConfiguredAgent.middle_step] Agent config value: '{agent_config.some_agent_value}'")
        return ConfiguredEventB(payload=agent_config.some_agent_value)

    @step()
    async def end_step(self, event: ConfiguredEventB) -> StopEvent:
        return StopEvent()
