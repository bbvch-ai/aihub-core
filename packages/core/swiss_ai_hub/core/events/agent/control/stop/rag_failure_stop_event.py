from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control.stop.rag_failure_reason import RAGFailureReason
from swiss_ai_hub.core.events.agent.control.stop.stop_event import StopEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class RAGFailureStopEvent(StopEvent):
    """Stop event emitted when a RAG run failed to produce a useful answer.

    The `reason` field tells the parent agent which path produced the failure — context insufficient,
    expert declined, expert errored, or a few-shot fallback that bypassed retrieval.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.rag_failure_stop_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.rag_failure_stop_event.description"
    )

    reason: Annotated[
        RAGFailureReason,
        Field(description="Why this run failed to produce a useful answer."),
    ]
