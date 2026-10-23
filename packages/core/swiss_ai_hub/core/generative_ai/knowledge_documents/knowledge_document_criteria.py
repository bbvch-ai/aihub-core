from typing import Annotated

from pydantic import BaseModel, Field


class KnowledgeDocumentCriteria(BaseModel):
    """One way to pick documents: every condition given must hold, conditions left out do not narrow."""

    path_glob: Annotated[
        str | None, Field(description="Glob on the path relative to the collection, e.g. 'invoices/2025/**'.")
    ] = None
    path_regex: Annotated[str | None, Field(description="Regular expression searched anywhere in the path.")] = None
    content_query: Annotated[
        str | None,
        Field(
            description="Only documents whose text contains this term, or matches it as a regex. Use terms that "
            "identify documents (a supplier, a number, a year, a contract party), never a word describing the "
            "records wanted, such as 'hardware': lines rarely contain it, so documents would be missed."
        ),
    ] = None
    content_is_regex: Annotated[bool, Field(description="Whether `content_query` is a regular expression.")] = False
    document_ids: Annotated[
        list[str], Field(description="Only these documents, by the ids a listing or a search returned.")
    ] = []
