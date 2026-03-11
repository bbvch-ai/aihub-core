from typing import ClassVar

from swiss_ai_hub.core.events.agent.user.UserMessageEvent import UserMessageEvent
from swiss_ai_hub.core.i18n.LocaleString import LocaleString

from playground.minimal_workflow.agent_in_the_loop_workflow.WorkerAgent.Events.ExtractNumberEvent import (
    ExtractNumberEvent,
)
from playground.minimal_workflow.agent_in_the_loop_workflow.WorkerAgent.Events.WorkerStopEvent import WorkerStopEvent
from swiss_ai_hub.agent.agents.Agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step


class WorkerAgent(Agent):
    """Worker agent for orchestration demo."""

    name: ClassVar[LocaleString] = LocaleString(
        en="Worker Agent", de="Arbeiter Agent", fr="Agent Travailleur", it="Agente Lavoratore"
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Worker agent for orchestration demo",
        de="Arbeiter Agent für Orchestrierungs Demo",
        fr="Agent travailleur pour démo orchestration",
        it="Agente lavoratore per demo orchestrazione",
    )
    icon: ClassVar[str] = "mage:settings"

    @step()
    async def start_step(self, event: UserMessageEvent) -> ExtractNumberEvent:
        print("[WorkerAgent.start_step]", event)
        return ExtractNumberEvent(number=int(event.messages[-1].content))

    @step()
    async def end_step(self, event: ExtractNumberEvent) -> WorkerStopEvent:
        print("[WorkerAgent.end_step]", event)
        return WorkerStopEvent(result=event.number * 2)
