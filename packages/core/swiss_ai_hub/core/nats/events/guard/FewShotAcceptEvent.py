from typing import ClassVar

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events.guard.GuardAcceptEvent import GuardAcceptEvent


class FewShotAcceptEvent(GuardAcceptEvent):
    """
    Event indicating that the few-shot guard accepted the request.

    This event is triggered when the few-shot guard determines that
    the user query is appropriate based on analysis of provided examples.
    It signifies that the request matches the patterns of acceptable queries
    demonstrated in the few-shot examples.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.few_shot_guard_accept_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.few_shot_guard_accept_event.description"
    )
