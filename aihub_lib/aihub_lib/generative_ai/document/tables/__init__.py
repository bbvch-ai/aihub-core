"""Shared utilities for markdown table creation and parsing.

This module centralizes table handling logic to ensure consistency between:
- Table creation (DoclingLoader converts Docling tables to markdown)
- Table refinement (refine_document_tables pipeline op uses LLM for structure detection)
- Table parsing (MarkdownStructuralNodeParser chunks tables for nodes)

Both operations must use compatible formats, so they are co-located here.
"""

from aihub_lib.generative_ai.document.tables.markdown_table import (
    TableRefinementMetadata,
    TableRefinementResult,
    TableRefinementStats,
    create_markdown_table,
    parse_markdown_table,
    refine_markdown_table_with_stats,
    split_dataframe_into_chunks,
)

__all__ = [
    "TableRefinementMetadata",
    "TableRefinementResult",
    "TableRefinementStats",
    "create_markdown_table",
    "parse_markdown_table",
    "refine_markdown_table_with_stats",
    "split_dataframe_into_chunks",
]
