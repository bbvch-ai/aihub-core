from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.events.agent import ControlEvent
from swiss_ai_hub.core.generative_ai import KnowledgeDocumentSummary

from swiss_ai_hub.agent.capabilities.record_extraction.extraction_run import ExtractionRun

type CellValue = str | float | int | bool | None


class DocumentExtractedEvent(ControlEvent):
    """What one document yielded: its rows, or why it yielded none. Every request ends in one, failure included,
    because the join waits for a result per document."""

    run: Annotated[ExtractionRun, Field(description="The extraction this document belongs to.")]
    request_event_id: Annotated[str, Field(description="The `DocumentExtractionRequestedEvent` this answers.")]
    document: Annotated[KnowledgeDocumentSummary, Field(description="The document extracted from.")]
    rows: Annotated[list[dict[str, CellValue]], Field(description="Field name to value, one entry per record.")] = []
    failure_reason: Annotated[str | None, Field(description="Why the document yielded nothing; none on success.")] = (
        None
    )
    partly_read: Annotated[
        bool, Field(description="Whether only parts of the document were read, so rows outside them may be missing.")
    ] = False
    rows_dropped: Annotated[
        int, Field(description="How many rows were left out to keep the event within the message size.", ge=0)
    ] = 0
