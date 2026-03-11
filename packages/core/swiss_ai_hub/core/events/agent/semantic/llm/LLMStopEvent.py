from typing import ClassVar

from swiss_ai_hub.core.i18n.LocaleString import LocaleString

from ...control.stop.StopEvent import StopEvent
from .LLMEvent import LLMEvent


class LLMStopEvent(LLMEvent, StopEvent):
    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.semantic_llm_stop_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.semantic_llm_stop_event.description"
    )
