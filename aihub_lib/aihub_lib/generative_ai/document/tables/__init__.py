"""Shared utilities for markdown table creation and parsing.

This module centralizes table handling logic to ensure consistency between:
- Table creation (DoclingLoader converts Docling tables to markdown)
- Table parsing (MarkdownStructuralNodeParser chunks tables for nodes)

Both operations must use compatible formats, so they are co-located here.
"""

from aihub_lib.generative_ai.document.tables.markdown_table import (
    TableRefinementMetadata,
    TableRefinementResult,
    TableRefinementStats,
    create_markdown_table,
    create_markdown_table_with_stats,
    parse_markdown_table,
    split_dataframe_into_chunks,
)

__all__ = [
    "TableRefinementMetadata",
    "TableRefinementResult",
    "TableRefinementStats",
    "create_markdown_table",
    "create_markdown_table_with_stats",
    "parse_markdown_table",
    "split_dataframe_into_chunks",
]
