from typing import Annotated, Any

from pydantic import Field
from swiss_ai_hub.core.generative_ai import LLMConfig

from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_fields import KnowledgeDocumentFields
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_config import RecordExtractionConfig


class RecordExtractionFields(KnowledgeDocumentFields, ConversationFields):
    """The extraction settings a blueprint's config gains by listing this mixin as a base.

    One mixin carries everything the capability reads, the documents' scope and the conversation's models included,
    because a capability names a single required config.
    """

    record_extraction: Annotated[
        RecordExtractionConfig,
        Field(description="How tables are extracted from knowledge documents.", title="Table Extraction"),
    ] = RecordExtractionConfig()

    def extraction_llm(self) -> LLMConfig:
        """The extracting model at temperature zero, whatever the main model's: the same document must yield the same
        rows on every run, which a sampled model does not."""
        task = self.llm.as_task_llm(self.record_extraction.extraction_model_name or self.llm.model_name)
        return task.model_copy(
            update={"default_parameter": task.default_parameter.model_copy(update={"temperature": 0.0})}
        )

    @classmethod
    def record_extraction_form_elements(cls) -> dict[str, Any]:
        """The form elements for this class's own fields, for a subclass's `as_form()` to spread."""
        return {"record_extraction": RecordExtractionConfig.as_form()}
