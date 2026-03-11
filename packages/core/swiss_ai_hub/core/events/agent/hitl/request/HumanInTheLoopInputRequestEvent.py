from typing import ClassVar, Literal

from swiss_ai_hub.core.events.agent.hitl.request.HumanInTheLoopRequestEvent import (
    HumanInTheLoopRequestEvent,
)
from swiss_ai_hub.core.i18n.LocaleString import LocaleString


class HumanInTheLoopInputRequestEvent(HumanInTheLoopRequestEvent):
    """Request free-form text input from a human operator."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.hitl_input_request_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_input_request_event.description"
    )

    hitl_type: Literal["input"] = "input"
