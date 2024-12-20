from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import StartEvent, StopEvent
from playground.ConfiguredAgent.ConfiguredAgentConfig import StartStepConfig, ConfiguredAgentAgentConfig
from playground.ConfiguredAgent.Events.EventA import EventA


class ConfiguredAgent(Agent):

    @step()
    async def start_step(self, event: StartEvent, start_config: StartStepConfig) -> EventA:
        print(f"[ConfiguredAgent.start_step] Step config value: '{start_config.some_step_value}'")
        return EventA()

    @step()
    async def end_step(self, event: EventA, agent_config: ConfiguredAgentAgentConfig) -> StopEvent:
        print(f"[ConfiguredAgent.end_step] Agent config value: '{agent_config.some_agent_value}'")
        return StopEvent()