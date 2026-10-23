from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.generative_ai import BucketNamespacePair


class ExtractionRun(BaseModel):
    """What every document of one extraction shares, carried on each of its events.

    The join counts results per extraction, so a run that extracts twice, as a model in a tool loop may, assembles
    each table from its own documents only; carrying the count on every event lets it do so from the result alone.
    """

    extraction_id: Annotated[str, Field(description="The `ExtractRecordsEvent` this extraction answers.")]
    file_count: Annotated[int, Field(description="How many documents the extraction waits for.", ge=1)]
    field_names: Annotated[list[str], Field(description="The schema's fields, the table's columns after the source.")]
    criteria: Annotated[str, Field(description="How the documents were selected, for the table's summary.")] = ""
    notices: Annotated[list[str], Field(description="What the summary must say besides the counts.")] = []
    cut_short: Annotated[
        bool, Field(description="Whether discovery or the selection stopped at a limit before extracting.")
    ] = False
    show_collection: Annotated[
        bool, Field(description="Whether the table names each row's collection, as when it spans several.")
    ] = False
    tool_call_id: Annotated[str | None, Field(description="The tool call the extraction answers, if any.")] = None
    collections: Annotated[
        list[BucketNamespacePair],
        Field(description="The collections the run may read, so rows it leaves for later are checked against them."),
    ] = []
    sample: Annotated[
        bool, Field(description="Whether these documents are a sample of a selection too large for one answer.")
    ] = False
    total_documents: Annotated[int, Field(description="Documents the whole selection holds.", ge=0)] = 0
    above_ceiling: Annotated[
        bool, Field(description="Whether more documents match than the profile resolves, so the total is a floor.")
    ] = False
    part: Annotated[int, Field(description="Which part of a pending extraction this is, from 1; 0 when whole.")] = 0
    parts: Annotated[int, Field(description="How many parts the pending extraction has.", ge=0)] = 0
    first_document: Annotated[int, Field(description="Position of the part's first document, from 1.", ge=0)] = 0
