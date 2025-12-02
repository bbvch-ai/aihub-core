import json
from typing import Annotated

from aihub_lib.generative_ai.document.refinement import refine_document_text_with_metadata
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from dagster import ConfigurableResource, ResourceDependency
from llama_index.core.schema import Document
from pydantic import Field

TEXT_REFINEMENT_METADATA_KEY = "text_refinement"


class TextRefinementResource(ConfigurableResource):
    """Resource for LLM-based text refinement to fix OCR errors and structural issues."""

    llm_config: ResourceDependency[LLMConfig]

    max_chunk_tokens: Annotated[
        int, Field(default=4000, description="Maximum tokens per chunk for text refinement.")
    ] = 4000

    def refine(self, document: Document) -> Document:
        """Refine document text using LLM.

        Stores refinement metadata in document.metadata under 'text_refinement' key.
        """
        result = refine_document_text_with_metadata(
            document.text, self.llm_config, max_chunk_tokens=self.max_chunk_tokens
        )

        # Merge existing metadata with refinement metadata (as JSON string for Dagster compatibility)
        updated_metadata = {**document.metadata} if document.metadata else {}
        updated_metadata[TEXT_REFINEMENT_METADATA_KEY] = json.dumps(result.metadata.model_dump())

        return Document(text=result.content, extra_info=document.extra_info, metadata=updated_metadata)
