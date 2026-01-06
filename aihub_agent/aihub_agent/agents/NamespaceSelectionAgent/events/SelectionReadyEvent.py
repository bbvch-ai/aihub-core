from typing import Annotated

from aihub_lib.nats.events import KnowledgeSource
from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from pydantic import Field


class SelectionReadyEvent(ControlEvent):
    """
    Emitted when namespace selection is complete and ready to proceed.

    This event triggers RAGAgent invocation after user approval
    or when maximum correction rounds have been reached.
    """

    selected_sources: Annotated[
        list[KnowledgeSource],
        Field(description="Final selected knowledge sources for RAG"),
    ]

    reasoning: Annotated[
        str,
        Field(description="Reasoning for the final selection"),
    ]
