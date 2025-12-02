"""Table refinement using LLM to detect table structure and split merged tables."""

import logging
import re
from typing import TYPE_CHECKING

import pandas as pd

from aihub_lib.generative_ai.document.tables import (
    TableRefinementMetadata,
    TableRefinementResult,
    create_markdown_table_with_stats,
)

if TYPE_CHECKING:
    from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig

_logger = logging.getLogger(__name__)


def refine_document_tables(markdown_text: str, llm_config: "LLMConfig") -> str:
    """Refine tables in markdown text using LLM to detect structure and split merged tables.

    Finds all markdown tables in the text and processes them with LLM to:
    - Detect multi-row headers
    - Split incorrectly merged tables
    - Fix column alignment errors

    Tables must already be wrapped in <table> tags (as produced by DoclingLoader).
    """
    result = refine_document_tables_with_metadata(markdown_text, llm_config)
    return result.content


def refine_document_tables_with_metadata(markdown_text: str, llm_config: "LLMConfig") -> TableRefinementResult:
    """Refine tables and return both refined content and metadata about what was done.

    Returns:
        TableRefinementResult with refined content and detailed metadata about refinements.
    """
    table_pattern = r"<table>(.*?)</table>"
    matches = list(re.finditer(table_pattern, markdown_text, re.DOTALL))

    if not matches:
        _logger.debug("No <table> tags found in document")
        return TableRefinementResult(
            content=markdown_text,
            metadata=TableRefinementMetadata(
                tables_processed=0,
                tables_split=0,
                total_tables_after_split=0,
                total_column_corrections=0,
                table_stats=[],
            ),
        )

    _logger.info(f"Refining {len(matches)} table(s) with LLM")

    result = markdown_text
    offset = 0
    table_stats = []
    tables_split = 0
    total_tables_after_split = 0
    total_column_corrections = 0

    for match in matches:
        table_content = match.group(1).strip()
        df = _parse_markdown_table_to_dataframe(table_content)

        if df is None or df.empty:
            _logger.debug("Could not parse table, skipping")
            continue

        refined_tables, stats = create_markdown_table_with_stats(df, llm_config)

        if stats:
            table_stats.append(stats)
            if stats.was_split:
                tables_split += 1
            total_tables_after_split += stats.tables_after_split
            total_column_corrections += stats.column_corrections_applied

        individual_tables = refined_tables.split("\n\n")
        wrapped_tables = "\n\n".join(f"<table>{t}</table>" for t in individual_tables if t.strip())

        start = match.start() + offset
        end = match.end() + offset
        result = result[:start] + wrapped_tables + result[end:]
        offset += len(wrapped_tables) - (end - start)

    metadata = TableRefinementMetadata(
        tables_processed=len(matches),
        tables_split=tables_split,
        total_tables_after_split=total_tables_after_split,
        total_column_corrections=total_column_corrections,
        table_stats=table_stats,
    )

    return TableRefinementResult(content=result, metadata=metadata)


def _parse_markdown_table_to_dataframe(markdown_table: str) -> pd.DataFrame | None:
    """Parse a markdown table into a DataFrame with integer column indices.

    Returns DataFrame with columns as integers (0, 1, 2, ...) so the LLM can
    analyze the full table including what would normally be the header row.
    """
    try:
        lines = markdown_table.strip().split("\n")
        if len(lines) < 2:
            return None

        header_line = lines[0]
        separator_line_idx = None
        for i, line in enumerate(lines[1:], 1):
            if re.match(r"^\|[\s:\-|]+\|$", line.strip()):
                separator_line_idx = i
                break

        if separator_line_idx is None:
            return None

        data_lines = lines[separator_line_idx + 1 :] if len(lines) > separator_line_idx + 1 else []

        headers = [col.strip() for col in header_line.split("|")[1:-1]]
        num_cols = len(headers)

        all_rows = [headers]
        for line in data_lines:
            row = [cell.strip() for cell in line.split("|")[1:-1]]
            if len(row) == num_cols:
                all_rows.append(row)

        if not all_rows:
            return None

        return pd.DataFrame(all_rows, columns=list(range(num_cols)))
    except (ValueError, IndexError, KeyError) as e:
        _logger.debug(f"Failed to parse markdown table: {e}")
        return None
