"""Document refinement utilities for document processing.

This module provides LLM-based cleanup for documents extracted from PDFs,
handling common issues like OCR errors, structural artifacts, and table formatting.
It also provides quality validation to detect severe parsing bugs.
"""

from aihub_lib.generative_ai.document.refinement.quality_validator import (
    QualityValidationResult,
    RepetitionIssue,
    validate_document_quality,
)
from aihub_lib.generative_ai.document.refinement.table_refiner import (
    refine_document_tables,
    refine_document_tables_with_metadata,
)
from aihub_lib.generative_ai.document.refinement.text_refiner import (
    TextRefinementMetadata,
    TextRefinementResult,
    refine_document_text,
    refine_document_text_with_metadata,
)

__all__ = [
    "QualityValidationResult",
    "RepetitionIssue",
    "TextRefinementMetadata",
    "TextRefinementResult",
    "refine_document_tables",
    "refine_document_tables_with_metadata",
    "refine_document_text",
    "refine_document_text_with_metadata",
    "validate_document_quality",
]
