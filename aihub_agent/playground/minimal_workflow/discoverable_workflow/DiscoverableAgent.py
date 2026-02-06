from typing import ClassVar

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StartEvent, StopEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step


class DiscoverableAgent(Agent):
    """Agent demonstrating discoverability patterns."""

    name: ClassVar[LocaleString] = LocaleString(
        en="Discoverable Agent", de="Entdeckbarer Agent", fr="Agent Découvrable", it="Agente Scopribile"
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Agent for discovery demo",
        de="Agent für Entdeckung Demo",
        fr="Agent pour démo découverte",
        it="Agente per demo scoperta",
    )
    icon: ClassVar[str] = "mage:search"

    @step()
    async def start_step(self, event: StartEvent) -> StopEvent:
        print("[DiscoverableAgent.start_step]", event)
        return StopEvent()
