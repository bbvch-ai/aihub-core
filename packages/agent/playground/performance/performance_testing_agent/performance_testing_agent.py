from typing import ClassVar

from swiss_ai_hub.core.events.agent import StartEvent, StopEvent
from swiss_ai_hub.core.i18n import LocaleString

from playground.performance.performance_testing_agent.events.parallel_event import ParallelEvent
from playground.performance.performance_testing_agent.performance_testing_agent_config import (
    PerformanceTestingAgentConfig,
)
from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
from swiss_ai_hub.agent.workflow.decorators.step import step


@precondition()
async def ensure_enough_events(parallel_events: list[ParallelEvent], config: PerformanceTestingAgentConfig) -> bool:
    return len(parallel_events) == config.number_of_events


class PerformanceTestingAgent(Agent):
    """Agent for performance testing."""

    name: ClassVar[LocaleString] = LocaleString(
        en="Performance Testing Agent",
        de="Performance Test Agent",
        fr="Agent Test Performance",
        it="Agente Test Performance",
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Agent for performance testing",
        de="Agent für Performance Tests",
        fr="Agent pour tests de performance",
        it="Agente per test di performance",
    )
    icon: ClassVar[str] = "mage:dashboard"

    @step()
    async def start_step(self, _: StartEvent, config: PerformanceTestingAgentConfig) -> list[ParallelEvent]:
        payload = "0" * config.payload_kb * 1024
        return [ParallelEvent(index=index, payload=payload) for index in range(config.number_of_events)]

    @step(precondition=ensure_enough_events)
    async def stop_step(self, _: list[ParallelEvent]) -> StopEvent:
        return StopEvent()
