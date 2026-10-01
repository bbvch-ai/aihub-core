from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.events.agent.control.control_event import ControlEvent


class RecallMemoryEvent(ControlEvent):
    """
    Asks the memory capability for what the profile remembers about the user and the organization, for a query.

    Built with `Memory.recall(...)`; answered with `MemoryRecalledEvent`, empty when memory is off for the
    profile or the run has no identity to read for.
    """

    query: Annotated[str, Field(description="The question to search memories with.")]
    org_memory_namespaces: Annotated[
        list[str],
        Field(description="Organization-memory namespaces to narrow the search to; empty means the profile's own."),
    ] = []
