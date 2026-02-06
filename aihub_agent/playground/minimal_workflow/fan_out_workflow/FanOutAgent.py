from typing import ClassVar

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent, StopEvent
from aihub_lib.nats.workflow.annotations.custom_types.ListOfSize import FixedList

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.fan_out_workflow.events.FanOutA import FanOutA
from playground.minimal_workflow.fan_out_workflow.events.FanOutB import FanOutB

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
