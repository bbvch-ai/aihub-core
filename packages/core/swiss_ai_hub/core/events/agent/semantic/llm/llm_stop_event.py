from typing import Annotated, Any, ClassVar

from pydantic import Field

from swiss_ai_hub.core.i18n.locale_string import LocaleString

from ...control.stop.stop_event import StopEvent
from .llm_event import LLMEvent


class LLMStopEvent(LLMEvent, StopEvent):
    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.semantic_llm_stop_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.semantic_llm_stop_event.description"
    )

    structured_output: Annotated[
        dict[str, Any] | None,
        Field(
            description="The answer parsed and validated against the `response_schema` the run was started with. "
            "The answer text holds the same JSON, so clients that read text only keep working.",
        ),
    ] = None
