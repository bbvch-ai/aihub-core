from typing import Annotated, ClassVar

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.guard.GuardRejectionEvent import GuardRejectionEvent


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

    new_query: Annotated[
        str | None,
        Field(description="A revised query to get better search results for additional context.", default=None),
    ]
