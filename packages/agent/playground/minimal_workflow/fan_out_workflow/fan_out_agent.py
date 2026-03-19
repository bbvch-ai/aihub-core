from typing import ClassVar

from swiss_ai_hub.core.events.agent import StartEvent, StopEvent
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.workflow.annotations.custom_types.list_of_size import FixedList

from playground.minimal_workflow.fan_out_workflow.events.fan_out_a import FanOutA
from playground.minimal_workflow.fan_out_workflow.events.fan_out_b import FanOutB
from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step

N = 5


class FanOutAgent(Agent):
    """Agent demonstrating fan-out parallel processing patterns."""

    name: ClassVar[LocaleString] = LocaleString(
        en="Fan Out Agent", de="Fan-Out Agent", fr="Agent Fan-Out", it="Agente Fan-Out"
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Agent for fan-out parallel processing",
        de="Agent für Fan-Out-Parallelverarbeitung",
        fr="Agent pour traitement parallèle fan-out",
        it="Agente per elaborazione parallela fan-out",
    )
    icon: ClassVar[str] = "mage:share"

    @step()
    async def start_step(self, _: StartEvent) -> list[FanOutA]:
        print("[start_step]")
        return [FanOutA(payload=str(i)) for i in range(N)]

    @step()
    async def process_a(self, event: FanOutA) -> FanOutB:
        return FanOutB(payload=event.payload)

    @step()
    async def stop_step(self, _: FixedList(FanOutB, N)) -> StopEvent:
        print("[stop_step]")
        return StopEvent()
