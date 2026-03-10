from typing import ClassVar

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events.guard.GuardAcceptEvent import GuardAcceptEvent


class ContextSufficientAcceptEvent(GuardAcceptEvent):
    """
    Event indicating that the context sufficiency guard accepted the request.

    This event is triggered when the context sufficiency guard determines that
    there is sufficient context available to answer the user's query without
    requiring additional information retrieval or processing.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.context_sufficient_accept_event.name"
    )
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.context_sufficient_accept_event.description"
    )
