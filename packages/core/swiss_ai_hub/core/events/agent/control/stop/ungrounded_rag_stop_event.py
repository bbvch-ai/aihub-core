from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control.stop.rag_stop_event import RAGStopEvent
from swiss_ai_hub.core.events.agent.control.stop.ungrounded_reason import UngroundedReason
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class UngroundedRAGStopEvent(RAGStopEvent):
    """Stop event emitted when a RAG run terminated without an answer grounded in retrieved context.

    The `reason` field tells the parent agent which path produced the ungrounded outcome — context
    insufficient, expert declined, expert errored, or a few-shot fallback that bypassed retrieval.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.ungrounded_rag_stop_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.ungrounded_rag_stop_event.description"
    )

    reason: Annotated[
        UngroundedReason,
        Field(description="Why this run did not produce a grounded answer."),
    ]
