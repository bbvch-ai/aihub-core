from typing import ClassVar

from swiss_ai_hub.core.i18n.locale_string import LocaleString

from ...control.stop.stop_event import StopEvent
from .llm_event import LLMEvent


class LLMStopEvent(LLMEvent, StopEvent):
    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.semantic_llm_stop_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.semantic_llm_stop_event.description"
    )
