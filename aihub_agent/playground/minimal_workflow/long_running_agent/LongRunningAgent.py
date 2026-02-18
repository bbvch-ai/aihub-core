import asyncio
from typing import ClassVar

from aihub_lib.displayers.EventDisplayer import EventDisplayer
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StopEvent, UserMessageEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step


class LongRunningAgent(Agent):
    """Agent demonstrating long-running task patterns."""

    name: ClassVar[LocaleString] = LocaleString(
        en="Long Running Agent", de="Lang laufender Agent", fr="Agent Long Durée", it="Agente Lunga Durata"
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Agent for long running demo",
        de="Agent für lang laufende Demo",
        fr="Agent pour démo longue durée",
        it="Agente per demo lunga durata",
    )
    icon: ClassVar[str] = "mage:clock"

    @step()
    async def start_step(self, _: UserMessageEvent, displayer: EventDisplayer) -> StopEvent:
        for i in range(20):
            await displayer.display_chunk(f"{i}\n", model_name="model")
            await asyncio.sleep(1)
        return StopEvent()
