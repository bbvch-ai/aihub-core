from typing import ClassVar

from swiss_ai_hub.core.events.agent.guard.GuardAcceptEvent import GuardAcceptEvent
from swiss_ai_hub.core.i18n.LocaleString import LocaleString


class SensitiveInfoAcceptEvent(GuardAcceptEvent):
    """
    Event indicating that the sensitive information guard accepted the response.

    This event is triggered when the sensitive information guard determines that
    the response does not contain any sensitive or confidential information and
    can be safely presented to the user without modifications.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.sensitive_info_accept_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.sensitive_info_accept_event.description"
    )
