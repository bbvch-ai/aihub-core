from typing import Annotated

from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from pydantic import Field


class StartNamespaceSelectionEvent(ControlEvent):
    """
    Triggers the namespace selection process.

    This event is emitted to initiate LLM-based namespace selection:
    - From topic_change_guard_step when this is the first query in a thread
    - From process_approval_step when user rejects and wants re-selection

    This is distinct from NamespaceSelectionEvent which carries the selection RESULT.
    """

    reasoning: Annotated[
        str,
        Field(description="Reason for triggering namespace selection"),
    ]
