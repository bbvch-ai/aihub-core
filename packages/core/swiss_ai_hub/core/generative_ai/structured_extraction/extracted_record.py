from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.structured_extraction.record_provenance import RecordProvenance

RecordValue = str | float | int | bool | None


class ExtractedRecord(BaseModel):
    """One record found in a document, keyed by the field names of the schema it was extracted with."""

    values: Annotated[
        dict[str, RecordValue], Field(description="Field name to value; None where the document is silent")
    ]
    provenance: Annotated[RecordProvenance, Field(description="Document the record was extracted from")]
