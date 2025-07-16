from aihub_lib.nats.events import StartEvent, StopEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.precondition import precondition
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.precondition_workflow.events.ParallelEvent import ParallelEvent
from playground.minimal_workflow.precondition_workflow.PreconditionAgentConfig import PreconditionAgentConfig


@precondition()
async def ensure_enough_events(parallel_events: list[ParallelEvent], config: PreconditionAgentConfig) -> bool:
    return len(parallel_events) == config.number_of_events


class PreconditionAgent(Agent):
    agent_config_type: type[PreconditionAgentConfig] = PreconditionAgentConfig

    @step()
    async def start_step(self, _: StartEvent, config: PreconditionAgentConfig) -> list[ParallelEvent]:
        return [ParallelEvent(payload=str(i)) for i in range(config.number_of_events)]

    @step(precondition=ensure_enough_events)
    async def stop_step(self, _: list[ParallelEvent]) -> StopEvent:
        return StopEvent()
