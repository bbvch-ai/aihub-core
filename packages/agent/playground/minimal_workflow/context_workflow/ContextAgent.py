from typing import ClassVar

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events import StopEvent

from playground.minimal_workflow.context_workflow.events.ContextEvent import ContextEvent
from playground.minimal_workflow.context_workflow.events.CustomStartEvent import (
    CustomStartEvent,
)
from swiss_ai_hub.agent.agents.Agent import Agent
from swiss_ai_hub.agent.context.run.RunContext import RunContext
from swiss_ai_hub.agent.context.thread.ThreadContext import ThreadContext
from swiss_ai_hub.agent.workflow.decorators.step import step


class ContextAgent(Agent):
    """Agent demonstrating context usage patterns."""

    name: ClassVar[LocaleString] = LocaleString(
        en="Context Agent", de="Kontext Agent", fr="Agent Contexte", it="Agente Contesto"
    )
    description: ClassVar[LocaleString] = LocaleString(
        en="Agent for context demo",
        de="Agent für Kontext Demo",
        fr="Agent pour démo contexte",
        it="Agente per demo contesto",
    )
    icon: ClassVar[str] = "mage:database"

    @step()
    async def start_step(
        self,
        event: CustomStartEvent,
        thread_context: ThreadContext,
        run_context: RunContext,
    ) -> ContextEvent:
        thread_count = await thread_context.get("count", 0)
        run_count = await run_context.get("count", 0)
        print(f"[SimpleAgent.start_step] Payload is '{event.payload}'")
        print(f"[SimpleAgent.start_step] Called {thread_count} times in thread, {run_count} times in run")
        await thread_context.set("count", thread_count + 1)
        await run_context.set("count", run_count + 1)
        return ContextEvent(thread_count=thread_count + 1, run_count=run_count + 1)

    @step()
    async def end_step(self, event: ContextEvent, thread_context: ThreadContext, run_context: RunContext) -> StopEvent:
        payload = await run_context.get("payload", [])
        print(f"[SimpleAgent.end_step] Payload is '{payload}'")

        thread_count = await thread_context.get("count", 0)
        run_count = await run_context.get("count", 0)
        print(f"[SimpleAgent.end_step] Called {thread_count} times in thread, {run_count} times in run")
        return StopEvent()
