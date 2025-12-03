import logging
import re
from typing import TYPE_CHECKING, Annotated

import pandas as pd
from llama_index.core import PromptTemplate
from pydantic import BaseModel, Field

from aihub_lib.generative_ai.document.tables.markdown_table import apply_header_rows, has_integer_column_indices

if TYPE_CHECKING:
    from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig

logger = logging.getLogger(__name__)


class TableBoundary(BaseModel):
    start_row: Annotated[int, Field(description="0-based index of first row of this table")]


class TableSplitAnalysis(BaseModel):
    tables: Annotated[
        list[TableBoundary],
        Field(description="List of table boundaries. First table always starts at row 0."),
    ]
    reasoning: Annotated[str, Field(description="Brief explanation of why tables were split or kept together")]


class HeaderAnalysis(BaseModel):
    num_header_rows: Annotated[int, Field(description="Number of header rows (1-4)")]
    reasoning: Annotated[str, Field(description="Brief explanation of header structure detected")]


class TableRefinementStats(BaseModel):
    original_rows: Annotated[int, Field(description="Number of rows in original table")]
    was_split: Annotated[bool, Field(description="Whether the table was split into multiple tables")]
    tables_after_split: Annotated[int, Field(description="Number of tables after splitting")]
    header_rows_detected: Annotated[list[int], Field(description="Header rows detected for each resulting table")]
    split_reasoning: Annotated[str, Field(description="LLM reasoning for split decision")]


class TableRefinementMetadata(BaseModel):
    tables_processed: Annotated[int, Field(description="Number of tables processed")]
    tables_split: Annotated[int, Field(description="Number of tables that were split")]
    total_tables_after_split: Annotated[int, Field(description="Total tables after all splitting")]
    table_stats: Annotated[list[TableRefinementStats], Field(description="Per-table statistics")]


class TableRefinementResult(BaseModel):
    content: Annotated[str, Field(description="Refined markdown content")]
    metadata: Annotated[TableRefinementMetadata, Field(description="Refinement statistics")]


def refine_document_tables_with_metadata(markdown_text: str, llm_config: "LLMConfig") -> TableRefinementResult:
    """
    Refine tables in markdown text using LLM to detect structure and split merged tables.

    Finds all markdown tables in the text and processes them with LLM to:
    - Detect multi-row headers
    - Split incorrectly merged tables

    Tables must already be wrapped in <table> tags (as produced by DoclingLoader).
    """
    table_pattern = r"<table>(.*?)</table>"
    matches = list(re.finditer(table_pattern, markdown_text, re.DOTALL))

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

    result = markdown_text
    offset = 0
    table_stats = []
    tables_split = 0
    total_tables_after_split = 0

    for match in matches:
        table_content = match.group(1).strip()
        df = _parse_markdown_table_to_dataframe(table_content)

        if df is None or df.empty:
            logger.debug("Could not parse table, skipping")
            continue

        refined_tables, stats = _refine_markdown_table_with_stats(df, llm_config)

        if stats:
            table_stats.append(stats)
            if stats.was_split:
                tables_split += 1
            total_tables_after_split += stats.tables_after_split

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
        table_stats=table_stats,
    )

    return TableRefinementResult(content=result, metadata=metadata)


def _refine_markdown_table_with_stats(
    df: pd.DataFrame, llm_config: "LLMConfig"
) -> tuple[str, TableRefinementStats | None]:
    """Refine a table using LLM and return statistics about the refinement."""
    if df.empty:
        return df.to_markdown(index=False), None

    original_rows = len(df)
    df = _reset_columns_to_data(df)
    table_for_llm = _format_table_with_row_indices(df)
    logger.debug(f"Analyzing table structure with LLM ({len(df)} rows)")
    logger.debug(f"Table input for LLM:\n{table_for_llm[:1000]}{'...' if len(table_for_llm) > 1000 else ''}")
    try:
        # Step 1: Detect table splits
        split_analysis = _detect_table_splits(table_for_llm, llm_config)
        logger.debug(f"Step 1 - Split detection: {len(split_analysis.tables)} table(s): {split_analysis.reasoning}")

        # Step 2: For each split table, detect headers and create markdown
        markdown_tables = []
        header_rows_detected = []

        for i, boundary in enumerate(split_analysis.tables):
            if i + 1 < len(split_analysis.tables):
                end_row = split_analysis.tables[i + 1].start_row
            else:
                end_row = len(df)

            table_df = df.iloc[boundary.start_row : end_row].copy()
            table_df = table_df.reset_index(drop=True)

            # Detect headers for this specific table
            table_for_analysis = _format_table_with_row_indices(table_df)
            header_analysis = _detect_header_rows(table_for_analysis, llm_config)
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

        return "\n\n".join(markdown_tables), stats
    except Exception as e:
        logger.warning(f"LLM table analysis failed, falling back to single header row: {e}")
        df = apply_header_rows(df, 1)
        return df.to_markdown(index=False), None


def _reset_columns_to_data(df: pd.DataFrame) -> pd.DataFrame:
    if has_integer_column_indices(df):
        return df

    header_row = pd.DataFrame([df.columns.tolist()], columns=range(len(df.columns)))
    data_rows = df.copy()
    data_rows.columns = range(len(df.columns))
    return pd.concat([header_row, data_rows], ignore_index=True)


def _format_cell_value(value: object) -> str:
    if pd.isna(value):
        return ""
    str_value = str(value).strip()
    if str_value.lower() in ("none", "nan", "<na>"):
        return ""
    return str_value


def _format_table_with_row_indices(df: pd.DataFrame) -> str:
    """Format DataFrame as text with explicit row indices for LLM analysis.

    Instead of markdown table format, uses a clearer format with row indices:
    [0] col1_value | col2_value | col3_value
    [1] col1_value | col2_value | col3_value

    Empty cells are represented as empty strings between pipes.
    Uses positional index (0, 1, 2...) regardless of DataFrame's actual index.
    """
    lines = []
    for idx, (_, row) in enumerate(df.iterrows()):
        row_values = " | ".join(_format_cell_value(v) for v in row.values)
        lines.append(f"[{idx}] {row_values}")
    return "\n".join(lines)


def _detect_table_splits(table_text: str, llm_config: "LLMConfig") -> TableSplitAnalysis:
    prompt_text = """Analyze this table data to detect if it contains multiple tables merged together.

SIGNS OF MERGED TABLES (split when you see these):
- Header-like rows appearing in the middle of data (column names, categories, or descriptive labels)
- A row that looks like it starts a new table (new column headers for a different dataset)
- Text like "Table 2:", "Tabelle:", or a table title/caption appearing mid-data
- Thematic break: data switches to a completely different subject
- Structural reset: the logical structure restarts (new date ranges, new categories, different metrics)

DO NOT split for:
- Empty rows used as visual separators within continuous data
- Subtotal or summary rows that are part of the same dataset
- Category grouping rows within the same table
- Minor formatting variations in data rows

Each row is prefixed with its 0-based index in square brackets: "[0]", "[1]", etc.

Table Data:
{table_text}

Return table boundaries. The first table always starts at row 0.
If this is a single table, return one entry with start_row=0.
If multiple tables are merged, return multiple entries with each table's starting row."""

    prompt = PromptTemplate(prompt_text)
    llm, _ = llm_config.to_llama_index()
    analysis = llm.structured_predict(TableSplitAnalysis, prompt, table_text=table_text)

    logger.debug(f"Split analysis raw response: {analysis.tables}, reasoning={analysis.reasoning}")

    # Validate: sort by start_row and ensure the first starts at 0
    validated = sorted(
        [TableBoundary(start_row=max(0, t.start_row)) for t in analysis.tables], key=lambda t: t.start_row
    )
    if not validated or validated[0].start_row != 0:
        validated = [TableBoundary(start_row=0)] + [t for t in validated if t.start_row > 0]

    return TableSplitAnalysis(tables=validated, reasoning=analysis.reasoning)


def _detect_header_rows(table_text: str, llm_config: "LLMConfig") -> HeaderAnalysis:
    prompt_text = """Analyze this table to determine how many header rows it has.

SIGNS OF MULTI-ROW HEADERS:
- First 1-4 rows contain column names, category labels, or groupings
- Hierarchical headers (e.g., "Q1 2024" with "Jan | Feb | Mar" below)
- Empty cells in header rows where labels span multiple columns
- Unit rows (e.g., "in CHF", "in thousands") below column names
- Subcategory rows that qualify the columns above

SIGNS THAT A ROW IS DATA (not a header):
- Contains numeric values, dates, or specific data points
- Follows a pattern consistent with other data rows
- Contains entity names that are being measured (companies, products, people)

Each row is prefixed with its 0-based index in square brackets: "[0]", "[1]", etc.

Table Data:
{table_text}

Return the number of header rows (1-4). Most tables have 1-2 header rows."""

    prompt = PromptTemplate(prompt_text)
    llm, _ = llm_config.to_llama_index()
    analysis = llm.structured_predict(HeaderAnalysis, prompt, table_text=table_text)

    logger.debug(f"Header analysis raw response: {analysis.num_header_rows}, reasoning={analysis.reasoning}")

    # Validate: clamp to 1-4
    validated_num = max(1, min(4, analysis.num_header_rows))
    return HeaderAnalysis(num_header_rows=validated_num, reasoning=analysis.reasoning)


def _parse_markdown_table_to_dataframe(markdown_table: str) -> pd.DataFrame | None:
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
        logger.debug(f"Failed to parse markdown table: {e}")
        return None
