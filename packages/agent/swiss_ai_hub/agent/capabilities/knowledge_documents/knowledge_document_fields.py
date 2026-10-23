from typing import Annotated, Any

from pydantic import Field

from swiss_ai_hub.agent.capabilities.knowledge.knowledge_tool_fields import KnowledgeToolFields
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_config import KnowledgeDocumentConfig


class KnowledgeDocumentFields(KnowledgeToolFields):
    """The document-tool settings a blueprint's config gains by listing this mixin as a base.

    It extends the knowledge-tool settings because the documents come from the same collections: one picker decides
    what both the vector search and the document tools may touch.
    """

    knowledge_documents: Annotated[
        KnowledgeDocumentConfig,
        Field(description="Whether and where the model may work on whole documents.", title="Knowledge Documents"),
    ] = KnowledgeDocumentConfig()

    @classmethod
    def knowledge_document_form_elements(cls) -> dict[str, Any]:
        """The form elements for this class's own fields, for a subclass's `as_form()` to spread."""
        return {"knowledge_documents": KnowledgeDocumentConfig.as_form()}
