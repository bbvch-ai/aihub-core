from typing import ClassVar

from swiss_ai_hub.core.events.agent import StartEvent, StopEvent
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step


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
