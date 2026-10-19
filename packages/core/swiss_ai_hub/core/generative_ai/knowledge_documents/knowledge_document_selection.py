from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_criteria import KnowledgeDocumentCriteria


class KnowledgeDocumentSelection(BaseModel):
    """The documents a request is about, described rather than listed: a document is selected when it meets any of the
    criteria.

    Describing the set keeps a model's tool call short however many files match, and lets the caller apply its own glob
    and limits when it resolves the set, so a model can only narrow what it was given.
    """

    any_of: Annotated[
        list[KnowledgeDocumentCriteria],
        Field(description="A document is selected when it meets every condition of at least one entry.", min_length=1),
    ]
