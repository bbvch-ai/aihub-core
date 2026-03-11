from typing import ClassVar

from swiss_ai_hub.core.events.agent.guard.GuardRejectionEvent import GuardRejectionEvent
from swiss_ai_hub.core.i18n.LocaleString import LocaleString


class FewShotRejectEvent(GuardRejectionEvent):
    """
    Event indicating that the few-shot guard rejected the request.

    This event is triggered when the few-shot guard determines that
    the user query is inappropriate based on analysis of provided examples.
    It signifies that the request does not match the patterns of acceptable queries
    demonstrated in the few-shot examples and should be blocked.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.few_shot_guard_reject_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.few_shot_guard_reject_event.description"
    )
