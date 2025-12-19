from typing import Annotated

from aihub_lib.nats.events import KnowledgeSource
from aihub_lib.nats.events.control.ControlEvent import ControlEvent
from pydantic import Field


class ClarificationNeededEvent(ControlEvent):
    """
    Emitted when more clarification is needed from the user.

    This event triggers the clarification loop, causing the workflow to
    ask the user a clarifying question before re-evaluating namespace selection.
    """

    current_sources: Annotated[
        list[KnowledgeSource],
        Field(description="Best-guess sources so far based on available information"),
    ]

    clarification_question: Annotated[
        str,
        Field(description="LLM-generated question to ask the user for clarification"),
    ]
