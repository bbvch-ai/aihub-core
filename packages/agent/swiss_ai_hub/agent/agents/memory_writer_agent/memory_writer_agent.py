from typing import ClassVar

from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.events.agent import StoreUserMemoryEvent, StoreUserMemoryRequestedEvent
from swiss_ai_hub.core.generative_ai import AgentMemory
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.agents.memory_writer_agent.events.memory_stored_stop_event import MemoryStoredStopEvent
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.workflow.decorators.step import step


class MemoryWriterAgent(Agent):
    """
    System agent that persists user memory in its own run, decoupled from the chat run's critical path
    (issue #1179). Triggered by a `MemoryStorageRequestedEvent` from a RAG agent; the RAG run finalizes as
    soon as the answer is ready and never waits on this write.

    It rebuilds the *originating* agent's `AgentMemory` from the identity carried on the event, so the
    fact-extraction prompt and the `_agent_id` scoping tag are identical to an inline write — the only
    difference is that the work runs here, in a separate, independently-traced execution context.
    """

    name: ClassVar[AgentLocaleString] = AgentLocaleString(
        de="Speicher-Writer", en="Memory Writer", fr="Écrivain mémoire", it="Scrittore memoria"
    )
    description: ClassVar[AgentLocaleString] = AgentLocaleString(
        de="Persistiert Nutzerspeicher ausserhalb des kritischen Pfads.",
        en="Persists user memory off the chat critical path.",
        fr="Persiste la mémoire utilisateur hors du chemin critique.",
        it="Persiste la memoria utente fuori dal percorso critico.",
    )
    icon: ClassVar[str] = "mdi:content-save"
    # System agent: triggered programmatically, never a user-facing blueprint — keep it out of the Admin UI.
    discoverable: ClassVar[bool] = False

    @step()
    async def store_step(self, event: StoreUserMemoryRequestedEvent, t: LocaleHandler) -> MemoryStoredStopEvent:
        """Persist the user memory using the originating agent's identity, then stop with the write summary."""
        memory = AgentMemory(
            agent_config=AgentConfig(
                agent_id=event.origin_agent_id,
                name=event.origin_agent_name,
                description=event.origin_agent_description,
            ),
            agent_class=event.origin_agent_class,
            t=t,
        )
        memory_added = await memory.add_user_memory(
            messages=event.messages,
            user_id=event.user.id,
            thread_id=event.origin_thread_id,
            display_id=event.origin_display_id,
            run_id=event.origin_run_id,
        )
        return MemoryStoredStopEvent.from_store_event(StoreUserMemoryEvent.from_memory_added_object(memory_added))
