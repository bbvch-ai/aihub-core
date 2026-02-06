from typing import ClassVar

from aihub_lib.i18n.LocaleString import LocaleString

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.custom_start_stop_events.events.MyCustomStartEvent import MyCustomStartEvent
from playground.minimal_workflow.custom_start_stop_events.events.MyCustomStopEvent import MyCustomStopEvent


class CustomStartStopEventAgent(Agent):
    """Agent demonstrating custom start/stop event patterns."""

    name: ClassVar[LocaleString] = LocaleString(
        en="Custom Events Agent",
        de="Benutzerdefinierte Events Agent",
        fr="Agent Événements Personnalisés",
        it="Agente Eventi Personalizzati",
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Agent for custom events demo",
        de="Agent für benutzerdefinierte Events Demo",
        fr="Agent pour démo événements personnalisés",
        it="Agente per demo eventi personalizzati",
    )
    icon: ClassVar[str] = "mage:bolt"

    @step()
    async def start_step(self, event: MyCustomStartEvent) -> MyCustomStopEvent:
        print("[SimpleAgent.start_step]", event)
        return MyCustomStopEvent(payload=event.payload)
