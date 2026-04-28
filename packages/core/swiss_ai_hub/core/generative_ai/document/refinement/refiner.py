import logging
import re
from typing import TYPE_CHECKING

import pandas as pd

from swiss_ai_hub.core.generative_ai.document.refinement.models import (
    TableRefinementMetadata,
    TableRefinementResult,
    TableRefinementStats,
)
from swiss_ai_hub.core.generative_ai.document.refinement.table_analyzer import TableAnalyzer
from swiss_ai_hub.core.generative_ai.document.tables.markdown_table import (
    apply_header_rows,
    format_for_llm,
    parse_markdown_table,
    wrap_tables_with_tags,
)

if TYPE_CHECKING:
    from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig

logger = logging.getLogger(__name__)

TABLE_PATTERN = re.compile(r"<table>(.*?)</table>", re.DOTALL)


def refine_document_tables_with_metadata(
    markdown_text: str,
    llm_config: "LLMConfig",
    extra_headers: dict[str, str] | None = None,
) -> TableRefinementResult:
    """
    Refine tables in markdown text using LLM to detect structure and split merged tables.

    Finds all markdown tables in the text and processes them with LLM to:
    - Detect multi-row headers
    - Split incorrectly merged tables

    Tables must already be wrapped in <table> tags (as produced by the document loaders).
    """
    matches = list(TABLE_PATTERN.finditer(markdown_text))

    if not matches:
        logger.debug("No <table> tags found in document")
        return TableRefinementResult(
            content=markdown_text,
            metadata=TableRefinementMetadata(
                tables_processed=0,
                tables_split=0,
                total_tables_after_split=0,
                table_stats=[],
            ),
        )

    logger.info(f"Refining {len(matches)} table(s) with LLM")

    analyzer = TableAnalyzer(llm_config, extra_headers=extra_headers)
    result = markdown_text
    offset = 0
    table_stats: list[TableRefinementStats] = []
    tables_split = 0
    total_tables_after_split = 0

    for match in matches:
        table_content = match.group(1).strip()
        df = parse_markdown_table(table_content, include_header_as_data=True)

        if df is None or df.empty:
            logger.debug(f"Could not parse table, skipping. Content preview: {table_content[:200]!r}")
            continue

        refined_tables, stats = _refine_single_table(df, analyzer)

        if stats:
            table_stats.append(stats)
            if stats.was_split:
                tables_split += 1
            total_tables_after_split += stats.tables_after_split

        wrapped_tables = wrap_tables_with_tags(refined_tables)

        start = match.start() + offset
        end = match.end() + offset
        result = result[:start] + wrapped_tables + result[end:]
        offset += len(wrapped_tables) - (end - start)

    return TableRefinementResult(
        content=result,
        metadata=TableRefinementMetadata(
            tables_processed=len(matches),
            tables_split=tables_split,
            total_tables_after_split=total_tables_after_split,
            table_stats=table_stats,
        ),
    )


def _refine_single_table(df: pd.DataFrame, analyzer: TableAnalyzer) -> tuple[list[str], TableRefinementStats | None]:
    """Process a single table: detect splits, detect headers, convert to markdown."""
    original_rows = len(df)
    table_for_llm = format_for_llm(df)

    logger.debug(f"Analyzing table structure with LLM ({len(df)} rows)")
    logger.debug(f"Table input for LLM:\n{table_for_llm[:1000]}{'...' if len(table_for_llm) > 1000 else ''}")

    try:
        # Step 1: Detect table splits
        split_analysis = analyzer.detect_splits(table_for_llm)
        logger.debug(f"Step 1 - Split detection: {len(split_analysis.tables)} table(s): {split_analysis.reasoning}")

        # Step 2: For each split table, detect headers and create markdown
        markdown_tables: list[str] = []
        header_rows_detected: list[int] = []

        for i, boundary in enumerate(split_analysis.tables):
            end_row = split_analysis.tables[i + 1].start_row if i + 1 < len(split_analysis.tables) else len(df)

            table_df = df.iloc[boundary.start_row : end_row].copy()
            table_df = table_df.reset_index(drop=True)

            # Detect headers for this specific table
            table_for_analysis = format_for_llm(table_df)
            header_analysis = analyzer.detect_headers(table_for_analysis)
            header_rows_detected.append(header_analysis.num_header_rows)

            logger.debug(
                f"  Table {i + 1} (rows {boundary.start_row}-{end_row - 1}): "
                f"{header_analysis.num_header_rows} header row(s): {header_analysis.reasoning}"
            )

            table_df = apply_header_rows(table_df, header_analysis.num_header_rows)
            markdown_tables.append(table_df.to_markdown(index=False))

        stats = TableRefinementStats(
            original_rows=original_rows,
            was_split=len(split_analysis.tables) > 1,
            tables_after_split=len(split_analysis.tables),
            header_rows_detected=header_rows_detected,
            split_reasoning=split_analysis.reasoning,
        )

        return markdown_tables, stats

    except Exception as e:
        logger.warning(f"LLM table analysis failed, falling back to single header row: {e}")
        df = apply_header_rows(df, 1)
        return [df.to_markdown(index=False)], None
