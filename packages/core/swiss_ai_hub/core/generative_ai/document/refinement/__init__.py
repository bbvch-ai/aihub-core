"""Table refinement module for detecting table structure using LLM."""

from swiss_ai_hub.core.generative_ai.document.refinement.models import (
    HeaderAnalysis,
    TableBoundary,
    TableRefinementMetadata,
    TableRefinementResult,
    TableRefinementStats,
    TableSplitAnalysis,
)
from swiss_ai_hub.core.generative_ai.document.refinement.refiner import refine_document_tables_with_metadata

__all__ = [
    "HeaderAnalysis",
    "TableBoundary",
    "TableRefinementMetadata",
    "TableRefinementResult",
    "TableRefinementStats",
    "TableSplitAnalysis",
    "refine_document_tables_with_metadata",
]
