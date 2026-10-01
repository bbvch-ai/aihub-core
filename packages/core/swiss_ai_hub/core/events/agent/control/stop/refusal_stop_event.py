from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control.stop.refusal_reason import RefusalReason
from swiss_ai_hub.core.events.agent.semantic.llm.llm_stop_event import LLMStopEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class RefusalStopEvent(LLMStopEvent):
    """Stop event for a turn the blueprint refused because of its input, not because of what it retrieved.

    Shaped as an `LLMStopEvent` so the refusal text reaches every consumer the way an answer does, through
    `output_messages`, while `reason` tells a programmatic caller what was wrong with the input. The
    retrieval outcomes stay on `RAGFailureStopEvent`; this one is shared by every conversational blueprint.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.refusal_stop_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.refusal_stop_event.description"
    )

    reason: Annotated[RefusalReason, Field(description="What about the input made the turn unanswerable.")]
