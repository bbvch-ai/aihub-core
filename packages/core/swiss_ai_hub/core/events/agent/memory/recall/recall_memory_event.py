from typing import Annotated, ClassVar

from pydantic import Field

from swiss_ai_hub.core.events.agent.control_and_display_event import ControlAndDisplayEvent
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class RecallMemoryEvent(ControlAndDisplayEvent):
    """
    Asks the memory capability for what the profile remembers about the user and the organization, for a query.

    Built with `Memory.recall(...)`; answered with `MemoryRecalledEvent`, empty when memory is off for the
    profile or the run has no identity to read for.
    """

    _display_name: ClassVar[LocaleString] = LocaleString.from_i18n_path("lib.events.recall_memory_event.name")
    _display_description: ClassVar[LocaleString] = LocaleString.from_i18n_path(
        "lib.events.recall_memory_event.description"
    )

    query: Annotated[str, Field(description="The question to search memories with.")]
    org_memory_namespaces: Annotated[
        list[str],
        Field(description="Organization-memory namespaces to narrow the search to; empty means the profile's own."),
    ] = []
    tool_call_id: Annotated[
        str | None,
        Field(description="The tool call this answers when the model chose it in a tool loop; none otherwise."),
    ] = None
