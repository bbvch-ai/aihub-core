from typing import ClassVar

from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.events.agent import ScheduledStartEvent, StopEvent
from swiss_ai_hub.core.i18n import LocaleString

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.workflow.decorators.step import step


class ScheduledDemoAgent(Agent):
    """Demo agent that runs on a cron schedule.

    Accepting `ScheduledStartEvent` — and nothing else — is the whole opt-in: discovery reports this
    class as schedulable, and because no step consumes a `UserMessageEvent` it stays out of the chat UI.
    """

    name: ClassVar[LocaleString] = LocaleString(
        en="Scheduled Demo Agent",
        de="Geplanter Demo-Agent",
        fr="Agent Démo Planifié",
        it="Agente Demo Pianificato",
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Demo agent that runs automatically on a cron schedule",
        de="Demo-Agent, der automatisch nach einem Cron-Zeitplan läuft",
        fr="Agent démo qui s'exécute automatiquement selon une planification cron",
        it="Agente demo che viene eseguito automaticamente secondo una pianificazione cron",
    )
    icon: ClassVar[str] = "mage:clock"

    @step()
    async def report_scheduled_run(self, event: ScheduledStartEvent, displayer: EventDisplayer) -> StopEvent:
        """Report the occurrence the run fired for, proving the schedule resolved to the expected time."""
        message = f"Scheduled run fired for occurrence {event.scheduled_for.isoformat()}"
        print(f"[ScheduledDemoAgent.report_scheduled_run] {message}")
        await displayer.display_chunk(message, model_name="ScheduledDemoAgent")
        return StopEvent()
