"""Markdown table utilities for creation, parsing, and chunking.

Co-locates table creation and parsing to ensure format compatibility.
"""

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Annotated

import pandas as pd
from llama_index.core import PromptTemplate
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig

_logger = logging.getLogger(__name__)


class TableBoundary(BaseModel):
    """Describes the boundary of a single table within merged data."""

    start_row: Annotated[int, Field(description="0-based index of first row of this table")]


class TableSplitAnalysis(BaseModel):
    """LLM response for table split detection (step 1)."""

    tables: Annotated[
        list[TableBoundary],
        Field(description="List of table boundaries. First table always starts at row 0."),
    ]
    reasoning: Annotated[str, Field(description="Brief explanation of why tables were split or kept together")]


class HeaderAnalysis(BaseModel):
    """LLM response for header row detection (step 2)."""

    num_header_rows: Annotated[int, Field(description="Number of header rows (1-4)")]
    reasoning: Annotated[str, Field(description="Brief explanation of header structure detected")]


class ColumnCorrection(BaseModel):
    """A single column correction to fix misaligned data."""

    row: Annotated[int, Field(description="0-based row index where the error occurs")]
    from_col: Annotated[int, Field(description="0-based column index where the value currently is")]
    to_col: Annotated[int, Field(description="0-based column index where the value should be")]


class ColumnAlignmentAnalysis(BaseModel):
    """LLM response for column alignment correction (step 3)."""

    corrections: Annotated[
        list[ColumnCorrection],
        Field(description="List of corrections needed. Empty list if table is correctly aligned."),
    ]
    reasoning: Annotated[str, Field(description="Brief explanation of alignment issues found or why table is correct")]


class TableRefinementStats(BaseModel):
    """Statistics for a single table's refinement."""

    original_rows: Annotated[int, Field(description="Number of rows in original table")]
    was_split: Annotated[bool, Field(description="Whether the table was split into multiple tables")]
    tables_after_split: Annotated[int, Field(description="Number of tables after splitting")]
    header_rows_detected: Annotated[list[int], Field(description="Header rows detected for each resulting table")]
    column_corrections_applied: Annotated[int, Field(description="Total column corrections applied")]
    split_reasoning: Annotated[str, Field(description="LLM reasoning for split decision")]


class TableRefinementMetadata(BaseModel):
    """Metadata about table refinement applied to a document."""

    tables_processed: Annotated[int, Field(description="Number of tables processed")]
    tables_split: Annotated[int, Field(description="Number of tables that were split")]
    total_tables_after_split: Annotated[int, Field(description="Total tables after all splitting")]
    total_column_corrections: Annotated[int, Field(description="Total column corrections applied")]
    table_stats: Annotated[list[TableRefinementStats], Field(description="Per-table statistics")]


class TableRefinementResult(BaseModel):
    """Result of table refinement including content and metadata."""

    content: Annotated[str, Field(description="Refined markdown content")]
    metadata: Annotated[TableRefinementMetadata, Field(description="Refinement statistics")]


# =============================================================================
# Table Creation (used by DoclingLoader)
# =============================================================================


def create_markdown_table(df: pd.DataFrame, llm_config: "LLMConfig | None" = None) -> str:
    """Create markdown table(s) from a DataFrame.

    With llm_config: Uses three-step LLM analysis:
      1. Detect and split merged tables
      2. Detect multi-row headers for each table
      3. Fix column alignment errors (data in wrong columns)
    Without: uses first row as header if columns are integers, else keeps as-is.
    """
    content, _ = _create_markdown_table_internal(df, llm_config)
    return content


def create_markdown_table_with_stats(
    df: pd.DataFrame, llm_config: "LLMConfig | None" = None
) -> tuple[str, TableRefinementStats | None]:
    """Create markdown table(s) from a DataFrame and return refinement statistics.

    Returns:
        Tuple of (markdown_content, stats). Stats is None if no LLM processing was done.
    """
    return _create_markdown_table_internal(df, llm_config)


def _create_markdown_table_internal(
    df: pd.DataFrame, llm_config: "LLMConfig | None" = None
) -> tuple[str, TableRefinementStats | None]:
    """Internal implementation that returns both content and stats."""
    if df.empty:
        return df.to_markdown(index=False), None

    if llm_config is not None:
        original_rows = len(df)
        df = _reset_columns_to_data(df)
        table_for_llm = _format_table_with_row_indices(df)
        _logger.debug(f"Analyzing table structure with LLM ({len(df)} rows)")
        _logger.debug(f"Table input for LLM:\n{table_for_llm[:1000]}{'...' if len(table_for_llm) > 1000 else ''}")
        try:
            # Step 1: Detect table splits
            split_analysis = _detect_table_splits(table_for_llm, llm_config)
            _logger.debug(
                f"Step 1 - Split detection: {len(split_analysis.tables)} table(s): {split_analysis.reasoning}"
            )

            # Step 2 & 3: For each split table, detect headers, fix alignment, and create markdown
            markdown_tables = []
            header_rows_detected = []
            total_corrections = 0

            for i, boundary in enumerate(split_analysis.tables):
                if i + 1 < len(split_analysis.tables):
                    end_row = split_analysis.tables[i + 1].start_row
                else:
                    end_row = len(df)

                table_df = df.iloc[boundary.start_row : end_row].copy()
                table_df = table_df.reset_index(drop=True)

                # Step 2: Detect headers for this specific table
                table_for_analysis = _format_table_with_row_indices(table_df)
                header_analysis = _detect_header_rows(table_for_analysis, llm_config)
                header_rows_detected.append(header_analysis.num_header_rows)
                _logger.debug(
                    f"  Table {i + 1} (rows {boundary.start_row}-{end_row - 1}): "
                    f"{header_analysis.num_header_rows} header row(s): {header_analysis.reasoning}"
                )

                # Step 3: Fix column alignment errors
                alignment_analysis = _detect_column_alignment_errors(table_for_analysis, llm_config)
                if alignment_analysis.corrections:
                    _logger.debug(
                        f"  Table {i + 1}: {len(alignment_analysis.corrections)} column fix(es): "
                        f"{alignment_analysis.reasoning}"
                    )
                    table_df = _apply_column_corrections(table_df, alignment_analysis.corrections)
                    total_corrections += len(alignment_analysis.corrections)

                table_df = _apply_header_rows(table_df, header_analysis.num_header_rows)
                markdown_tables.append(table_df.to_markdown(index=False))

            stats = TableRefinementStats(
                original_rows=original_rows,
                was_split=len(split_analysis.tables) > 1,
                tables_after_split=len(split_analysis.tables),
                header_rows_detected=header_rows_detected,
                column_corrections_applied=total_corrections,
                split_reasoning=split_analysis.reasoning,
            )

            return "\n\n".join(markdown_tables), stats
        except Exception as e:
            _logger.warning(f"LLM table analysis failed, falling back to single header row: {e}")
            df = _apply_header_rows(df, 1)
    elif _has_integer_column_indices(df):
        df = _apply_header_rows(df, 1)

    return df.to_markdown(index=False), None


def _reset_columns_to_data(df: pd.DataFrame) -> pd.DataFrame:
    """Convert column names back to a data row so LLM can analyze the full table."""
    if _has_integer_column_indices(df):
        return df

    header_row = pd.DataFrame([df.columns.tolist()], columns=range(len(df.columns)))
    data_rows = df.copy()
    data_rows.columns = range(len(df.columns))
    return pd.concat([header_row, data_rows], ignore_index=True)


def _has_integer_column_indices(df: pd.DataFrame) -> bool:
    return all(isinstance(col, int) for col in df.columns)


def _format_cell_value(value: object) -> str:
    """Format cell value, normalizing empty/null values to empty string."""
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
    """Step 1: Detect if the table contains multiple merged tables that should be split."""
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

    _logger.debug(f"Split analysis raw response: {analysis.tables}, reasoning={analysis.reasoning}")

    # Validate: sort by start_row and ensure first starts at 0
    validated = sorted(
        [TableBoundary(start_row=max(0, t.start_row)) for t in analysis.tables], key=lambda t: t.start_row
    )
    if not validated or validated[0].start_row != 0:
        validated = [TableBoundary(start_row=0)] + [t for t in validated if t.start_row > 0]

    return TableSplitAnalysis(tables=validated, reasoning=analysis.reasoning)


def _detect_header_rows(table_text: str, llm_config: "LLMConfig") -> HeaderAnalysis:
    """Step 2: Detect how many header rows a table has."""
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

    _logger.debug(f"Header analysis raw response: {analysis.num_header_rows}, reasoning={analysis.reasoning}")

    # Validate: clamp to 1-4
    validated_num = max(1, min(4, analysis.num_header_rows))
    return HeaderAnalysis(num_header_rows=validated_num, reasoning=analysis.reasoning)


def _detect_column_alignment_errors(table_text: str, llm_config: "LLMConfig") -> ColumnAlignmentAnalysis:
    """Step 3: Detect and fix column alignment errors where data is in the wrong column."""
    prompt_text = """Analyze this table for column alignment errors where values are in the wrong column.

COMMON ALIGNMENT ERRORS:
- A value appears in the wrong column due to OCR or parsing errors
- Header text shifted into a data column or vice versa
- Values displaced by one or more columns (often due to empty cells being mishandled)
- Numeric data appearing in a text column or text in a numeric column

HOW TO DETECT ERRORS:
- Compare each cell's content type with what the column typically contains
- Look for values that don't match the pattern of other values in the same column
- Check if a value would make more sense in an adjacent column
- Identify rows where the data pattern is inconsistent with other rows

IMPORTANT:
- Only report actual errors, not stylistic differences
- Each correction moves ONE value from one column to another
- The target column's current value will be replaced (usually it's empty or wrong)
- Row and column indices are 0-based

Each row is prefixed with its 0-based index in square brackets: "[0]", "[1]", etc.
Columns are separated by " | " and are numbered 0, 1, 2, ... from left to right.

Table Data:
{table_text}

Return a list of corrections. Each correction specifies: row index, source column, target column.
Return an empty list if the table is correctly aligned."""

    prompt = PromptTemplate(prompt_text)
    llm, _ = llm_config.to_llama_index()
    analysis = llm.structured_predict(ColumnAlignmentAnalysis, prompt, table_text=table_text)

    _logger.debug(f"Alignment analysis raw response: {len(analysis.corrections)} corrections, {analysis.reasoning}")

    return analysis


def _apply_column_corrections(df: pd.DataFrame, corrections: list[ColumnCorrection]) -> pd.DataFrame:
    """Apply column corrections to fix misaligned data."""
    df = df.copy()
    num_rows, num_cols = df.shape

    for correction in corrections:
        # Validate indices
        if not (0 <= correction.row < num_rows):
            _logger.warning(f"Skipping correction: row {correction.row} out of bounds (0-{num_rows - 1})")
            continue
        if not (0 <= correction.from_col < num_cols):
            _logger.warning(f"Skipping correction: from_col {correction.from_col} out of bounds (0-{num_cols - 1})")
            continue
        if not (0 <= correction.to_col < num_cols):
            _logger.warning(f"Skipping correction: to_col {correction.to_col} out of bounds (0-{num_cols - 1})")
            continue

        # Move value from source to target column
        value = df.iloc[correction.row, correction.from_col]
        df.iloc[correction.row, correction.to_col] = value
        df.iloc[correction.row, correction.from_col] = ""

        _logger.debug(
            f"  Moved '{value}' from row {correction.row} col {correction.from_col} to col {correction.to_col}"
        )

    return df


def _apply_header_rows(df: pd.DataFrame, num_header_rows: int) -> pd.DataFrame:
    """Apply header rows. Multi-row headers are joined with " - " separator."""
    if num_header_rows <= 0:
        return df

    if num_header_rows == 1:
        df.columns = df.iloc[0]
        df = df[1:].reset_index(drop=True)
        df.columns.name = None
    elif num_header_rows <= len(df):
        header_rows = [df.iloc[i].tolist() for i in range(num_header_rows)]
        merged_headers = [" - ".join(str(val) for val in col_values) for col_values in zip(*header_rows)]
        df.columns = merged_headers
        df = df.iloc[num_header_rows:]
        df.reset_index(drop=True, inplace=True)

    return df


# =============================================================================
# Table Parsing (used by MarkdownStructuralNodeParser)
# =============================================================================


def parse_markdown_table(markdown_table: str) -> pd.DataFrame | None:
    """Parse a markdown table (pandas to_markdown format) into a DataFrame."""
    try:
        lines = markdown_table.strip().split("\n")
        if len(lines) < 2:
            return None

        header_line = lines[0]
        data_lines = lines[2:] if len(lines) > 2 else []

        headers = [col.strip() for col in header_line.split("|")[1:-1]]

        data = []
        for line in data_lines:
            row = [cell.strip() for cell in line.split("|")[1:-1]]
            if len(row) == len(headers):
                data.append(row)

        if not headers:
            return None

        return pd.DataFrame(data, columns=headers)
    except Exception:
        return None


# =============================================================================
# Table Chunking (used by MarkdownStructuralNodeParser for large tables)
# =============================================================================


def split_dataframe_into_chunks(
    df: pd.DataFrame,
    max_tokens: int,
    token_counter: Callable[[str], int],
) -> list[str]:
    """Split a DataFrame into markdown table chunks. Each chunk includes headers."""
    TOKEN_COUNT_FIELD = "__token_count__"

    header_df = df.head(0)
    header_markdown = header_df.to_markdown(index=False)
    header_token_count = token_counter(header_markdown)

    available_tokens = max_tokens - header_token_count

    def count_row_tokens(row: pd.Series) -> int:
        row_text = " | ".join(str(val) for val in row.values)
        row_with_pipes = f"| {row_text} |"
        return token_counter(row_with_pipes)

    df = df.copy()
    df[TOKEN_COUNT_FIELD] = df.apply(count_row_tokens, axis=1)

    chunks: list[str] = []
    chunk_start = 0

    while chunk_start < len(df):
        cumsum = df[TOKEN_COUNT_FIELD].iloc[chunk_start:].cumsum()
        valid_rows = cumsum[cumsum <= available_tokens]

        if len(valid_rows) == 0:
            chunk_end = chunk_start + 1
        else:
            chunk_end = chunk_start + len(valid_rows)

        chunk_df = df.iloc[chunk_start:chunk_end].drop(columns=[TOKEN_COUNT_FIELD])
        markdown_table = chunk_df.to_markdown(index=False)
        chunks.append(markdown_table)

        chunk_start = chunk_end

    return chunks
