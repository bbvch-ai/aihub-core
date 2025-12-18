from typing import Annotated, ClassVar

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.human_in_the_loop.request.HumanInTheLoopConfirmationRequestEvent import (
    HumanInTheLoopConfirmationRequestEvent,
)
from aihub_lib.nats.events.human_in_the_loop.response.HumanInTheLoopResponseEvent import HumanInTheLoopResponseEvent


class HumanInTheLoopConfirmationResponseEvent(HumanInTheLoopResponseEvent):
    """Response containing yes/no confirmation from a human operator."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_confirmation_response_event.name"
    )
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_confirmation_response_event.description"
    )

    response: Annotated[bool, Field(description="The human operator's confirmation (True for yes, False for no).")]
    request_event: Annotated[
        HumanInTheLoopConfirmationRequestEvent,
        Field(description="The original confirmation request event."),
    ]
