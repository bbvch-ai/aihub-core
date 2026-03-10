from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events.human_in_the_loop.request.HumanInTheLoopInputRequestEvent import (
    HumanInTheLoopInputRequestEvent,
)
from swiss_ai_hub.core.nats.events.human_in_the_loop.response.HumanInTheLoopResponseEvent import (
    HumanInTheLoopResponseEvent,
)


class HumanInTheLoopInputResponseEvent(HumanInTheLoopResponseEvent[HumanInTheLoopInputRequestEvent]):
    """Response containing free-form text input from a human operator."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.hitl_input_response_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_input_response_event.description"
    )

    response: Annotated[str, Field(description="The human operator's text input.")]
