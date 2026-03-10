from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events.semantic import GuardEvent


class GuardRejectionEvent(GuardEvent):
    """
    Base class for all guard rejection events.

    This event is triggered when a guard mechanism determines that a request
    does not meet security, policy, or validation requirements and must be blocked.
    Guard rejection events are critical for maintaining system security and ensuring
    only authorized and valid requests proceed through the workflow.

    ### Why GuardRejectionEvent?
    Safeguarding the system from invalid requests is a critical part of any system. This event
    is used to communicate the reason for the rejection to the client and halt processing
    of potentially harmful or invalid requests.

    All specific guard rejection events should inherit from this base class
    to ensure consistent behavior and proper event handling throughout the system.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.guard_rejection_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.guard_rejection_event.description"
    )

    reason: Annotated[str, Field(description="Reason why the Guard rejected the request.")]
