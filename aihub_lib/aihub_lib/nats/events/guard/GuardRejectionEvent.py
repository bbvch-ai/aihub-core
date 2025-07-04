from typing import Annotated, ClassVar

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString

from ..control import StopEvent


class GuardRejectionEvent(StopEvent):
    """
    A class representing a guard rejection event.
    This event is used to communicate the reason for the rejection to the client.


    ### Why GuardRejectionEvent?
    Safeguarding the system from invalid requests is a critical part of any system. This event
    is used to communicate the reason for the rejection to the client.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.guard_rejection_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.guard_rejection_event.description"
    )

    reason: Annotated[str, Field(description="Reason why the Guard rejected the request.")]
