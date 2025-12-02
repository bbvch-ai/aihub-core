from typing import Annotated

from aihub_lib.generative_ai.document.refinement import refine_document_text
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from dagster import ConfigurableResource, ResourceDependency
from llama_index.core.schema import Document
from pydantic import Field


class TextRefinementResource(ConfigurableResource):
    """Resource for LLM-based text refinement to fix OCR errors and structural issues."""

    llm_config: ResourceDependency[LLMConfig]

    max_chunk_tokens: Annotated[
        int, Field(default=4000, description="Maximum tokens per chunk for text refinement.")
    ] = 4000

    def refine(self, document: Document) -> Document:
        """Refine document text using LLM."""
        refined_text = refine_document_text(document.text, self.llm_config, max_chunk_tokens=self.max_chunk_tokens)
        return Document(text=refined_text, extra_info=document.extra_info, metadata=document.metadata)
