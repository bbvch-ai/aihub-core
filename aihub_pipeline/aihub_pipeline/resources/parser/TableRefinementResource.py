from aihub_lib.generative_ai.document.refinement import refine_document_tables_with_metadata
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from dagster import ConfigurableResource, ResourceDependency
from llama_index.core.schema import Document

TABLE_REFINEMENT_METADATA_KEY = "table_refinement"


class TableRefinementResource(ConfigurableResource):
    """Resource for LLM-based table refinement to detect structure and split merged tables."""

    llm_config: ResourceDependency[LLMConfig]

    def refine(self, document: Document) -> Document:
        """Refine tables in document using LLM.

        Stores refinement metadata in document.metadata under 'table_refinement' key.
        """
        result = refine_document_tables_with_metadata(document.text, self.llm_config)

        # Merge existing metadata with refinement metadata
        updated_metadata = {**document.metadata} if document.metadata else {}
        updated_metadata[TABLE_REFINEMENT_METADATA_KEY] = result.metadata.model_dump()

        return Document(text=result.content, extra_info=document.extra_info, metadata=updated_metadata)
