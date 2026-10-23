from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.selection_fallback_criteria import SelectionFallbackCriteria
from swiss_ai_hub.agent.capabilities.record_extraction.extract_records_arguments import ExtractRecordsArguments


class SelectionFallbackAnswer(BaseModel):
    """The selection a model states when asked after its searches, or that nothing matches.

    Strict structured output needs at least one condition in `any_of`, so without the flag a model that found nothing
    would have to invent a selection, and its documents would be extracted. The entries offer no document ids: the
    fallback names documents by path and identifying text, not by which ones its searches showed.
    """

    any_of: Annotated[
        list[SelectionFallbackCriteria],
        Field(
            description="The documents to extract from: a document counts when it meets every condition of at least "
            "one entry. An entry without conditions selects every document in scope.",
            min_length=1,
        ),
    ]
    fields: Annotated[str, Field(description="The table's columns in the user's words.", min_length=1)]
    instructions: Annotated[
        str | None, Field(description="Which rows to keep, in the user's words; null when every row is wanted.")
    ] = None
    row_terms: Annotated[
        str | None, Field(description="Words or a regular expression the lines holding the wanted rows contain.")
    ] = None
    nothing_matches: Annotated[
        bool,
        Field(
            description="True when the searches found no document the request is about; the selection is then "
            "ignored and nothing is extracted."
        ),
    ] = False

    def as_arguments(self, by_location: bool) -> ExtractRecordsArguments:
        """The selection to extract; `by_location` keeps only path conditions, for a search stopped at its limit."""
        entries = [entry.by_location() if by_location else entry for entry in self.any_of]
        return ExtractRecordsArguments(
            any_of=[entry.as_criteria() for entry in entries],
            fields=self.fields,
            instructions=self.instructions,
            row_terms=self.row_terms,
        )
