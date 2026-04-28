from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.events.agent.control.stop.stop_event import StopEvent


class RAGStopEvent(StopEvent):
    """Common ancestor for RAG run terminations.

    Concrete subclasses (`RAGSuccessStopEvent`, `RAGFailureStopEvent`) share the `answer`
    payload so non-streaming consumers can read the final assistant text from a single
    terminal event regardless of the run's outcome.
    """

    answer: Annotated[
        str | None,
        Field(description="Final assistant answer text, populated for non-streaming consumers."),
    ] = None
