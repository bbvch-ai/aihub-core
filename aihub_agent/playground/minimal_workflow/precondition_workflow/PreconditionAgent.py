from typing import List

from aihub_agent.agents.abstract.Agent import Agent
from aihub_agent.workflow.decorators.precondition import precondition
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import StopEvent, StartEvent
from playground.minimal_workflow.precondition_workflow.PreconditionAgentConfig import PreconditionAgentConfig
from playground.minimal_workflow.precondition_workflow.events.ParallelEvent import ParallelEvent


@precondition()
def ensure_enough_events(parallel_events: List[ParallelEvent], config: PreconditionAgentConfig) -> bool:
    return len(parallel_events) == config.number_of_events


class PreconditionAgent(Agent):
    @step()
    async def start_step(self, _: StartEvent, config: PreconditionAgentConfig) -> List[ParallelEvent]:
        return [ParallelEvent(payload=str(i)) for i in range(config.number_of_events)]

    @step(precondition=ensure_enough_events)
    async def stop_step(self, _: List[ParallelEvent]) -> StopEvent:
        return StopEvent()
