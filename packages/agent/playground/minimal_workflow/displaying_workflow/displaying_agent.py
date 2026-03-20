from typing import ClassVar

from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import StartEvent, StopEvent
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step


class DisplayingAgent(Agent):
    """Agent demonstrating display event patterns."""

    name: ClassVar[LocaleString] = LocaleString(
        en="Displaying Agent", de="Anzeige Agent", fr="Agent Affichage", it="Agente Display"
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Agent for display demo",
        de="Agent für Anzeige Demo",
        fr="Agent pour démo affichage",
        it="Agente per demo display",
    )
    icon: ClassVar[str] = "mage:television"

    @step()
    async def start_step(self, event: StartEvent, displayer: EventDisplayer) -> StopEvent:
        print("[DisplayingAgent.start_step]", event)
        await displayer.display_thought("Let me think....")
        await displayer.display_chunk("This is some chunk that is sent to the user", model_name="gpt-4")
        return StopEvent()
