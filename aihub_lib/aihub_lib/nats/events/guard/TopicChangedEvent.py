from typing import Annotated, ClassVar

from pydantic import Field

from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.events.rag import KnowledgeSource
from aihub_lib.nats.events.semantic import GuardEvent


class TopicChangedEvent(GuardEvent):
    """
    Event indicating that the topic change guard detected a topic change.

    This event is triggered when the LLM-based topic change guard determines that
    the user's query is about a different topic than before. This signals that
    the agent should ask the user whether to search different knowledge sources.

    Unlike a rejection event, this doesn't stop the workflow - it triggers a
    human-in-the-loop interaction to confirm source re-selection.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.topic_changed_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.topic_changed_event.description"
    )

    reasoning: Annotated[
        str,
        Field(description="LLM's reasoning for why the topic changed."),
    ]

    current_sources: Annotated[
        list[KnowledgeSource],
        Field(description="The currently selected knowledge sources."),
    ]
