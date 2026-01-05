from typing import Annotated, ClassVar

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.guard.GuardAcceptEvent import GuardAcceptEvent
from aihub_lib.nats.events.rag import KnowledgeSource


class TopicUnchangedAcceptEvent(GuardAcceptEvent):
    """
    Event indicating that the topic change guard determined the topic is unchanged.

    This event is triggered when the LLM-based topic change guard determines that
    the user's query is about the same topic as before, and the previous namespace
    selection can be reused without re-selection or user confirmation.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.topic_unchanged_accept_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.topic_unchanged_accept_event.description"
    )

    current_sources: Annotated[
        list[KnowledgeSource],
        Field(description="The currently selected knowledge sources to reuse."),
    ]
