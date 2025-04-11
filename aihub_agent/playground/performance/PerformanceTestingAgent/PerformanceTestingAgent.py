from typing import List

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.precondition import precondition
from aihub_agent.workflow.decorators.step import step
from aihub_lib.nats.events import StopEvent, StartEvent
from playground.performance.PerformanceTestingAgent.PerformanceTestingAgentConfig import PerformanceTestingAgentConfig
from playground.performance.PerformanceTestingAgent.events.ParallelEvent import ParallelEvent


@precondition()
async def ensure_enough_events(parallel_events: List[ParallelEvent], config: PerformanceTestingAgentConfig) -> bool:
    return len(parallel_events) == config.number_of_events


class PerformanceTestingAgent(Agent):
    @step()
    async def start_step(self, _: StartEvent, config: PerformanceTestingAgentConfig) -> List[ParallelEvent]:
        payload = "0" * config.payload_kb * 1024
        return [ParallelEvent(index=index, payload=payload) for index in range(config.number_of_events)]

    @step(precondition=ensure_enough_events)
    async def stop_step(self, _: List[ParallelEvent]) -> StopEvent:
        return StopEvent()
