from typing import Annotated, ClassVar, Literal

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.human_in_the_loop.request.HumanInTheLoopRequestEvent import HumanInTheLoopRequestEvent


class HumanInTheLoopConfirmationRequestEvent(HumanInTheLoopRequestEvent):
    """Request yes/no confirmation from a human operator."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_confirmation_request_event.name"
    )
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_confirmation_request_event.description"
    )

    hitl_type: Annotated[
        Literal["confirmation"],
        Field(default="confirmation", description="Fixed to 'confirmation' for yes/no requests."),
    ] = "confirmation"
