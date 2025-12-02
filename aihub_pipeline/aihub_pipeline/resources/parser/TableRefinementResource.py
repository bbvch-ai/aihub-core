from aihub_lib.generative_ai.document.refinement import refine_document_tables
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from dagster import ConfigurableResource, ResourceDependency
from llama_index.core.schema import Document


class TableRefinementResource(ConfigurableResource):
    """Resource for LLM-based table refinement to detect structure and split merged tables."""

    llm_config: ResourceDependency[LLMConfig]

    def refine(self, document: Document) -> Document:
        """Refine tables in document using LLM."""
        refined_text = refine_document_tables(document.text, self.llm_config)
        return Document(text=refined_text, extra_info=document.extra_info, metadata=document.metadata)
