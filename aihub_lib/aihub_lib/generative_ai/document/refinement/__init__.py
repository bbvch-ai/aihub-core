"""Document refinement utilities for document processing.

This module provides LLM-based cleanup for documents extracted from PDFs,
handling common issues like OCR errors, structural artifacts, and table formatting.
"""

from aihub_lib.generative_ai.document.refinement.table_refiner import refine_document_tables
from aihub_lib.generative_ai.document.refinement.text_refiner import refine_document_text

__all__ = [
    "refine_document_tables",
    "refine_document_text",
]
