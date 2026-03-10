from typing import ClassVar

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events import StartEvent, StopEvent
from swiss_ai_hub.core.nats.events.human_in_the_loop import HumanInTheLoopInput

from swiss_ai_hub.agent.agents.Agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step


class HumanInTheLoopAgent(Agent):
    """Agent demonstrating human-in-the-loop patterns."""

    name: ClassVar[LocaleString] = LocaleString(
        en="Human In The Loop Agent",
        de="Human-in-the-Loop Agent",
        fr="Agent Humain dans la Boucle",
        it="Agente Human-in-the-Loop",
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Agent for HITL demo", de="Agent für HITL Demo", fr="Agent pour démo HITL", it="Agente per demo HITL"
    )
    icon: ClassVar[str] = "mage:user-check"

    @step()
    async def start_step(self, event: StartEvent) -> HumanInTheLoopInput.request:
        print("[HumanInTheLoopAgent.start_step]")
        return HumanInTheLoopInput.invoke(question="Shall I continue?")

    @step()
    async def end_step(self, event: HumanInTheLoopInput.response) -> StopEvent:
        print(
            "[HumanInTheLoopAgent.end_step]",
            event.request_event.question,
            event.response,
        )
        return StopEvent()
