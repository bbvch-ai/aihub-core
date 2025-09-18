from typing import Annotated, ClassVar

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.control.ControlEvent import ControlEvent


class GuardAcceptEvent(ControlEvent):
    """
    Base class for all guard acceptance events.

    This event is triggered when a guard mechanism determines that a request
    meets all security, policy, and validation requirements and can proceed.
    Guard events are critical for maintaining system security and ensuring
    proper workflow control.

    All specific guard acceptance events should inherit from this base class
    to ensure consistent behavior and proper event handling throughout the system.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.guard_accept_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.guard_accept_event.description"
    )

    reason: Annotated[str, Field(description="Reason why the guard accepted the request.")]
