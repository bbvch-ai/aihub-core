from typing import Annotated

from aihub_lib.nats.events import KnowledgeSource
from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from pydantic import Field


class NamespaceSelectionEvent(ControlEvent):
    """
    Result of namespace selection by the LLM.

    Represents the LLM's analysis of which namespaces are relevant for a user query,
    along with confidence scoring and reasoning for observability.
    """

    selected_sources: Annotated[
        list[KnowledgeSource],
        Field(description="Knowledge sources selected by the LLM"),
    ]

    confidence: Annotated[
        float,
        Field(description="Confidence score (0.0-1.0) in the selection", ge=0.0, le=1.0),
    ]

    reasoning: Annotated[
        str,
        Field(description="LLM's reasoning for the selection"),
    ]

    requires_clarification: Annotated[
        bool,
        Field(description="Whether the selection requires user clarification"),
    ] = False
