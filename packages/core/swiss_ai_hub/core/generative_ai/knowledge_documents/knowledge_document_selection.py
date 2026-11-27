from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.knowledge_documents.document_metadata_filter import DocumentMetadataFilter
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_criteria import KnowledgeDocumentCriteria
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_date_range import PathDateRange


class KnowledgeDocumentSelection(BaseModel):
    """The documents a request is about, described rather than listed: a document is selected when it meets any of the
    criteria.

    Describing the set keeps a model's tool call short however many files match, and lets the caller apply its own glob
    and limits when it resolves the set, so a model can only narrow what it was given. A selection has one period,
    applied after the entries to all they selected, because a request names its period once, and so is its metadata
    filter.
    """

    any_of: Annotated[
        list[KnowledgeDocumentCriteria],
        Field(description="A document is selected when it meets every condition of at least one entry.", min_length=1),
    ]
    path_date_range: Annotated[
        PathDateRange | None,
        Field(
            description="Leaves out the selected documents whose path dates them outside this period, such as a year "
            "folder, 2026-03 or 20260406 in a file name; a document whose path gives no clear date is kept."
        ),
    ] = None
    metadata_filter: Annotated[
        DocumentMetadataFilter | None,
        Field(
            description="Leaves out the selected documents whose ingested type or attributes fail this filter, after "
            "the period; a document that was not classified, or whose value is empty, is kept."
        ),
    ] = None
