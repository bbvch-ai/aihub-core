from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.events.agent import ControlEvent

from swiss_ai_hub.agent.agents.release_notes_agent.changelog_entry import ChangelogEntry


class ReleaseNotesWrittenEvent(ControlEvent):
    """The changelog in the writing language, shown and handed on to be translated.

    It carries the entries and their notes rather than the tickets: a note is a sentence, where a ticket's description
    can be pages, and every event is persisted and traced. A release at its cap of a few hundred tickets stays far below
    NATS' limit.
    """

    version: Annotated[str, Field(description="The version name as Jira spells it.")]
    entries: Annotated[list[ChangelogEntry], Field(description="Every entry, in changelog order.")]
    shown: Annotated[str, Field(description="The changelog exactly as the chat showed it.")]
