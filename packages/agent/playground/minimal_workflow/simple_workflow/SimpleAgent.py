from typing import ClassVar

from swiss_ai_hub.core.events.agent import StopEvent, UserMessageEvent
from swiss_ai_hub.core.i18n import LocaleString

from playground.minimal_workflow.simple_workflow.events.SimpleEventA import SimpleEventA
from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step


class SimpleAgent(Agent):
    """A simple agent demonstrating basic workflow patterns."""

    name: ClassVar[LocaleString] = LocaleString(
        en="Simple Agent", de="Einfacher Agent", fr="Agent Simple", it="Agente Semplice"
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Simple agent for demo purposes",
        de="Einfacher Agent für Demozwecke",
        fr="Agent simple pour démo",
        it="Agente semplice per demo",
    )
    icon: ClassVar[str] = "mage:play"

    @step()
    async def start_step(self, event: UserMessageEvent) -> SimpleEventA:
        print("[SimpleAgent.start_step]", event)
        return SimpleEventA(payload=event.messages[-1].content)

    @step()
    async def end_step(self, event: SimpleEventA) -> StopEvent:
        print("[SimpleAgent.end_step]", event)
        return StopEvent()
