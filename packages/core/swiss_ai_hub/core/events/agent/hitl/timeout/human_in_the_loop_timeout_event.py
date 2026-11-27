from typing import ClassVar

from swiss_ai_hub.core.events.agent.control.timeout.in_the_loop_timeout_event import InTheLoopTimeoutEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class HumanInTheLoopTimeoutEvent(InTheLoopTimeoutEvent):
    """The person asked by a `HumanInTheLoopRequestEvent` did not answer within its `timeout_seconds`."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.hitl_timeout_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.hitl_timeout_event.description"
    )
