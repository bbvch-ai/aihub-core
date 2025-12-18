from typing import Annotated, ClassVar

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.human_in_the_loop.request.HumanInTheLoopInputRequestEvent import (
    HumanInTheLoopInputRequestEvent,
)
from aihub_lib.nats.events.human_in_the_loop.response.HumanInTheLoopResponseEvent import HumanInTheLoopResponseEvent


class HumanInTheLoopInputResponseEvent(HumanInTheLoopResponseEvent):
    """Response containing free-form text input from a human operator."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.hitl_input_response_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_input_response_event.description"
    )

    response: Annotated[str, Field(description="The human operator's text input.")]
    request_event: Annotated[
        HumanInTheLoopInputRequestEvent,
        Field(description="The original input request event."),
    ]
