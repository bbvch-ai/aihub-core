from typing import ClassVar

from swiss_ai_hub.core.events.agent.guard.guard_rejection_event import GuardRejectionEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ExpertRejectEvent(GuardRejectionEvent):
    """
    Event indicating that expert escalation was rejected by the user.

    This event is triggered when a user declines the offer to escalate
    their question to a human expert after the system determined that
    the available context is insufficient to answer their query.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.expert_reject_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.expert_reject_event.description"
    )
