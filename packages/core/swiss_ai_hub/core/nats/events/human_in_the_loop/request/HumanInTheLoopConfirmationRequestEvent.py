from typing import ClassVar, Literal

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events.human_in_the_loop.request.HumanInTheLoopRequestEvent import (
    HumanInTheLoopRequestEvent,
)


class HumanInTheLoopConfirmationRequestEvent(HumanInTheLoopRequestEvent):
    """Request yes/no confirmation from a human operator."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_confirmation_request_event.name"
    )
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_confirmation_request_event.description"
    )

    hitl_type: Literal["confirmation"] = "confirmation"
