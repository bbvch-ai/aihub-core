from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.events.agent import ControlEvent
from swiss_ai_hub.core.generative_ai import KnowledgeDocumentSummary, RecordSchema

from swiss_ai_hub.agent.capabilities.record_extraction.extraction_run import ExtractionRun


class DocumentExtractionRequestedEvent(ControlEvent):
    """One document of an extraction to read, emitted once per document so they are extracted in parallel."""

    run: Annotated[ExtractionRun, Field(description="The extraction this document belongs to.")]
    document: Annotated[KnowledgeDocumentSummary, Field(description="The document to extract from.")]
    record_schema: Annotated[RecordSchema, Field(description="The fields every row has.")]
    instructions: Annotated[str | None, Field(description="Which records to keep.")] = None
    row_terms: Annotated[
        str | None, Field(description="What lines holding wanted records usually contain, for long documents.")
    ] = None
