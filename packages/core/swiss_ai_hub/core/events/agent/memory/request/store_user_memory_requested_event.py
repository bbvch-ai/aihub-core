from typing import Annotated, ClassVar

from llama_index.core.base.llms.types import ChatMessage, MessageRole
from pydantic import Field

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.events.agent.control.start.start_event import StartEvent
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class StoreUserMemoryRequestedEvent(StartEvent):
    """
    Start event for the `MemoryWriterAgent`: persist user memory in an independent run, off the chat run's
    critical path (issue #1179).

    It runs in a different execution context than the originating RAG run and cannot read that run's
    `run_context`, so it carries everything the writer needs as plain serializable data. The originating
    agent's identity (class/id/name/description) is carried explicitly so the writer rebuilds the *same*
    `AgentMemory` — preserving the agent-specific fact-extraction prompt and the `_agent_id` scoping tag.

    Scope: user memory only. Organization memory has a different API shape and is not on #1179's critical
    path; if it is decoupled later, add a `memory_type` discriminator here.
    """

    _display_name: ClassVar[LocaleString] = LocaleString(
        de="Nutzerspeicher schreiben",
        en="Store user memory",
        fr="Enregistrer la mémoire utilisateur",
        it="Salva memoria utente",
    )
    _display_description: ClassVar[LocaleString] = LocaleString(
        de="Persistiert Nutzererinnerungen ausserhalb des kritischen Pfads.",
        en="Persists user memories off the chat critical path.",
        fr="Persiste les mémoires utilisateur hors du chemin critique.",
        it="Persiste le memorie utente fuori dal percorso critico.",
    )

    locale: Annotated[
        str, Field(description="Originating run's locale, so extraction prompts stay in the user's language.")
    ] = LocaleHandler.DEFAULT_LOCALE
    user: Annotated[UserIdentity, Field(description="User the memories belong to.")]
    messages: Annotated[list[ChatMessage], Field(description="Conversation the writer extracts user memories from.")]
    origin_thread_id: Annotated[str, Field(description="Originating run's thread id, kept as memory metadata.")]
    origin_display_id: Annotated[str, Field(description="Originating run's display id, kept as memory metadata.")]
    origin_run_id: Annotated[str, Field(description="Originating run's run id, kept as memory metadata.")]
    origin_agent_class: Annotated[
        str, Field(description="Originating agent's class — rebuilds the same AgentMemory (prompt + _agent_id tag).")
    ]
    origin_agent_id: Annotated[str, Field(description="Originating agent's id — part of the _agent_id scoping tag.")]
    origin_agent_name: Annotated[
        LocaleString, Field(description="Originating agent's name — used in the fact-extraction prompt.")
    ]
    origin_agent_description: Annotated[
        LocaleString, Field(description="Originating agent's description — used in the fact-extraction prompt.")
    ]

    @property
    def user_query(self) -> str:
        """Last user message content — used as the trace input so the writer run is attributed to the query."""
        user_messages = [message for message in self.messages if message.role == MessageRole.USER]
        return (user_messages[-1].content or "") if user_messages else ""
