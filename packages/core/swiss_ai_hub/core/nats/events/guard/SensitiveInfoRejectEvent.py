from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events.guard.GuardRejectionEvent import GuardRejectionEvent


class SensitiveInfoRejectEvent(GuardRejectionEvent):
    """
    Event indicating that the sensitive information guard rejected the response.

    This event is triggered when the sensitive information guard determines that
    the response contains sensitive or confidential information. The event includes
    a cleaned version of the response with the sensitive information removed.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.sensitive_info_reject_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.sensitive_info_reject_event.description"
    )

    cleaned_answer: Annotated[str, Field(description="The revised response with sensitive information removed.")]
