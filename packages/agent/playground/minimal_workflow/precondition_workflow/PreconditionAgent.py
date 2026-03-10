from typing import ClassVar

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events import StartEvent, StopEvent

from playground.minimal_workflow.precondition_workflow.events.ParallelEvent import ParallelEvent
from playground.minimal_workflow.precondition_workflow.PreconditionAgentConfig import PreconditionAgentConfig
from swiss_ai_hub.agent.agents.Agent import Agent
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
from swiss_ai_hub.agent.workflow.decorators.step import step


@precondition()
async def ensure_enough_events(parallel_events: list[ParallelEvent], config: PreconditionAgentConfig) -> bool:
    return len(parallel_events) == config.number_of_events


class PreconditionAgent(Agent):
    """Agent demonstrating precondition patterns."""

    name: ClassVar[LocaleString] = LocaleString(
        en="Precondition Agent", de="Vorbedingung Agent", fr="Agent Précondition", it="Agente Precondizione"
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Agent for precondition demo",
        de="Agent für Vorbedingung Demo",
        fr="Agent pour démo précondition",
        it="Agente per demo precondizione",
    )
    icon: ClassVar[str] = "mage:check-circle"

    @step()
    async def start_step(self, _: StartEvent, config: PreconditionAgentConfig) -> list[ParallelEvent]:
        return [ParallelEvent(payload=str(i)) for i in range(config.number_of_events)]

    @step(precondition=ensure_enough_events)
    async def stop_step(self, _: list[ParallelEvent]) -> StopEvent:
        return StopEvent()
