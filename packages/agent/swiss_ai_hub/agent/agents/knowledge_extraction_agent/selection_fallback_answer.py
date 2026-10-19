from typing import Annotated

from pydantic import Field

from swiss_ai_hub.agent.capabilities.record_extraction.extract_records_arguments import ExtractRecordsArguments


class SelectionFallbackAnswer(ExtractRecordsArguments):
    """The selection a model states when asked after its searches, or that nothing matches.

    Strict structured output needs at least one condition in `any_of`, so without the flag a model that found nothing
    would have to invent a selection, and its documents would be extracted.
    """

    nothing_matches: Annotated[
        bool,
        Field(
            description="True when the searches found no document the request is about; the selection is then "
            "ignored and nothing is extracted."
        ),
    ] = False
