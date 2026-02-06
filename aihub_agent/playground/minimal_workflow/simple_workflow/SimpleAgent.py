from typing import ClassVar

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events import StopEvent, UserMessageEvent

from aihub_agent.agents.Agent import Agent
from aihub_agent.workflow.decorators.step import step
from playground.minimal_workflow.simple_workflow.events.SimpleEventA import SimpleEventA


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
