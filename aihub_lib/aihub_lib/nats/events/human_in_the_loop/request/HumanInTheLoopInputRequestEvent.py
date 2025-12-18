from typing import Annotated, ClassVar, Literal

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.human_in_the_loop.request.HumanInTheLoopRequestEvent import HumanInTheLoopRequestEvent


class HumanInTheLoopInputRequestEvent(HumanInTheLoopRequestEvent):
    """Request free-form text input from a human operator."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.hitl_input_request_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_input_request_event.description"
    )

    hitl_type: Annotated[
        Literal["input"],
        Field(default="input", description="Fixed to 'input' for text input requests."),
    ] = "input"
