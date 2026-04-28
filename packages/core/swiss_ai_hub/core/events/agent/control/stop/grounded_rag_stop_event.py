from typing import ClassVar

from swiss_ai_hub.core.events.agent.control.stop.rag_stop_event import RAGStopEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class GroundedRAGStopEvent(RAGStopEvent):
    """Stop event emitted when a RAG run produced an answer grounded in retrieved context."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.grounded_rag_stop_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.grounded_rag_stop_event.description"
    )
