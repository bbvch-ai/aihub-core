from typing import Annotated, Self

from pydantic import Field

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_plain_answer import (
    ExtractionRequestPlainAnswer,
)


class ExtractionRequestAnswer(ExtractionRequestPlainAnswer):
    """A chat message read as a table request over the profile's whole scope: the columns, which rows to keep, the
    places the user named, and the terms that order the documents. Strict structured output requires every field, so
    each has a value for "none"; the terms come last, so an output cut short loses only them."""

    row_terms: Annotated[
        str | None, Field(description="Words or a regular expression the lines holding the wanted rows contain.")
    ]
    document_terms: Annotated[
        str | None,
        Field(description="Words or a regular expression the documents holding wanted rows contain, e.g. a supplier."),
    ]

    @classmethod
    def without_terms(cls, plain: ExtractionRequestPlainAnswer) -> Self:
        return cls(**plain.model_dump(), row_terms=None, document_terms=None)
