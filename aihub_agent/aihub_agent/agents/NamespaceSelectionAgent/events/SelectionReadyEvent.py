from typing import Annotated

from aihub_lib.nats.events import KnowledgeSource
from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from pydantic import Field


class SelectionReadyEvent(ControlEvent):
    """
    Emitted when namespace selection is complete and ready to proceed.

    This event exits the clarification loop and triggers RAGAgent invocation.
    Selection is considered ready when either:
    - Confidence is above threshold
    - Maximum clarification rounds have been reached
    """

    selected_sources: Annotated[
        list[KnowledgeSource],
        Field(description="Final selected knowledge sources for RAG"),
    ]

    reasoning: Annotated[
        str,
        Field(description="Reasoning for the final selection"),
    ]
