from typing import ClassVar

from swiss_ai_hub.core.events.agent.control.timeout.in_the_loop_timeout_event import InTheLoopTimeoutEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class AgentInTheLoopTimeoutEvent(InTheLoopTimeoutEvent):
    """The agent a run delegated to did not stop or fail within the request's `timeout_seconds`."""

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.aitl_timeout_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.aitl_timeout_event.description"
    )
