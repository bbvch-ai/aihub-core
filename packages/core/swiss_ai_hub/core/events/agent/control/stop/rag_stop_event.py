from typing import ClassVar

from swiss_ai_hub.core.events.agent.control.stop.stop_event import StopEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class RAGStopEvent(StopEvent):
    """Abstract stop event for RAG-style agent runs.

    Concrete runs emit one of two subclasses: `GroundedRAGStopEvent` when the answer was grounded in
    retrieved context, or `UngroundedRAGStopEvent` (carrying a reason) when no grounded answer was
    produced. Parent agents (e.g. via `AgentInTheLoop`) can type their step on the abstract base to
    match any RAG outcome, on a concrete subclass to branch on grounded vs ungrounded, or read
    `UngroundedRAGStopEvent.reason` for fine-grained dispatch.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.rag_stop_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.rag_stop_event.description")
