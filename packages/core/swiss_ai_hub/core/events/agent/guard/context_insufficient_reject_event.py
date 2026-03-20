from typing import ClassVar

from swiss_ai_hub.core.events.agent.guard.guard_rejection_event import GuardRejectionEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class ContextInsufficientRejectEvent(GuardRejectionEvent):
    """
    Event indicating that the context sufficiency guard rejected the request.

    This event is triggered when the context sufficiency guard determines that
    there is insufficient context available to answer the user's query and
    additional information retrieval or processing is required. The event includes
    a new query suggestion for additional context retrieval.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.context_insufficient_reject_event.name"
    )
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.context_insufficient_reject_event.description"
    )
