from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.generative_ai import KnowledgeDocumentCriteria


class SelectionFallbackCriteria(BaseModel):
    """One way the fallback names documents: by what they are, never by ids a search happened to show.

    Searches made to check a condition on the rows show only the documents they reached, so a selection of their ids
    narrows the table to those, silently.
    """

    path_glob: Annotated[str | None, Field(description="Glob on the path, e.g. 'contracts/**'.")] = None
    path_regex: Annotated[str | None, Field(description="Regular expression searched anywhere in the path.")] = None
    content_query: Annotated[
        str | None, Field(description="Text identifying the documents, such as a supplier, a number or a year.")
    ] = None
    content_is_regex: Annotated[bool, Field(description="Whether `content_query` is a regular expression.")] = False

    def by_location(self) -> Self:
        """Only the conditions on the path: what a stopped search found in the text is incomplete."""
        return self.model_copy(update={"content_query": None, "content_is_regex": False})

    def as_criteria(self) -> KnowledgeDocumentCriteria:
        return KnowledgeDocumentCriteria(**self.model_dump())
