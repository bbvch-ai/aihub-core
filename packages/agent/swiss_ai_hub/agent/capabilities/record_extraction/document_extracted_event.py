from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.events.agent import ControlEvent
from swiss_ai_hub.core.generative_ai import KnowledgeDocumentSummary

from swiss_ai_hub.agent.capabilities.record_extraction.extraction_run import ExtractionRun


class DocumentExtractedEvent(ControlEvent):
    """What one document yielded: where its rows are stored, or why it yielded none. Every request ends in one,
    failure included, because the join waits for a result per document.

    The rows themselves are in object storage (`ExtractionFileStore`): a document can yield hundreds of long rows, and
    the join reads every result of the extraction each time one arrives.
    """

    run: Annotated[ExtractionRun, Field(description="The extraction this document belongs to.")]
    request_event_id: Annotated[str, Field(description="The `DocumentExtractionRequestedEvent` this answers.")]
    document: Annotated[KnowledgeDocumentSummary, Field(description="The document extracted from.")]
    rows_key: Annotated[
        str | None, Field(description="The stored rows of the document; none when it yielded none or failed.")
    ] = None
    row_count: Annotated[int, Field(description="How many rows the document yielded.", ge=0)] = 0
    unsure_count: Annotated[
        int, Field(description="How many of them may not meet the row condition and are marked for checking.", ge=0)
    ] = 0
    failure_reason: Annotated[str | None, Field(description="Why the document yielded nothing; none on success.")] = (
        None
    )
    partly_read: Annotated[
        bool, Field(description="Whether only parts of the document were read, so rows outside them may be missing.")
    ] = False
