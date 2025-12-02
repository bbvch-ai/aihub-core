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


class TableSegment(BaseModel):
    """Describes a single table within potentially merged data."""

    start_row: Annotated[int, Field(description="0-based index of first row of this table (including its header)")]
    num_header_rows: Annotated[int, Field(description="Number of header rows for this table (1-3 typical)")]


class TableStructureAnalysis(BaseModel):
    """LLM response for table structure analysis."""

    tables: Annotated[
        list[TableSegment],
        Field(
            description="List of tables found in the data. Each table has a start_row and num_header_rows. "
            "If only one table, start_row should be 0."
        ),
    ]
    reasoning: Annotated[str, Field(description="Brief explanation of the table structure detected")]


# =============================================================================
# Table Creation (used by DoclingLoader)
# =============================================================================


def create_markdown_table(df: pd.DataFrame, llm_config: "LLMConfig | None" = None) -> str:
    """Create markdown table(s) from a DataFrame.

    With llm_config: detects multi-row headers and splits merged tables.
    Without: uses first row as header if columns are integers, else keeps as-is.
    """
    if df.empty:
        return df.to_markdown(index=False)

    if llm_config is not None:
        df = _reset_columns_to_data(df)
        table_for_llm = _format_table_with_row_indices(df)
        _logger.debug(f"Analyzing table structure with LLM ({len(df)} rows)")
        _logger.debug(f"Table input for LLM:\n{table_for_llm[:1000]}{'...' if len(table_for_llm) > 1000 else ''}")
        try:
            analysis = _analyze_table_structure_with_llm(table_for_llm, llm_config)
            _logger.debug(f"LLM detected {len(analysis.tables)} table(s): {analysis.reasoning}")
            for i, seg in enumerate(analysis.tables):
                _logger.debug(f"  Table {i + 1}: start_row={seg.start_row}, num_header_rows={seg.num_header_rows}")
            return _apply_table_structure(df, analysis)
        except Exception as e:
            _logger.warning(f"LLM table analysis failed, falling back to single header row: {e}")
            df = _apply_header_rows(df, 1)
    elif _has_integer_column_indices(df):
        df = _apply_header_rows(df, 1)

    return df.to_markdown(index=False)


def _apply_table_structure(df: pd.DataFrame, analysis: TableStructureAnalysis) -> str:
    """Apply detected table structure to create properly formatted markdown tables."""
    if not analysis.tables:
        return _apply_header_rows(df, 1).to_markdown(index=False)

    markdown_tables = []

    for i, segment in enumerate(analysis.tables):
        if i + 1 < len(analysis.tables):
            end_row = analysis.tables[i + 1].start_row
        else:
            end_row = len(df)

        table_df = df.iloc[segment.start_row : end_row].copy()
        table_df = table_df.reset_index(drop=True)
        table_df = _apply_header_rows(table_df, segment.num_header_rows)

        markdown_tables.append(table_df.to_markdown(index=False))

    return "\n\n".join(markdown_tables)


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


def _analyze_table_structure_with_llm(table_markdown: str, llm_config: "LLMConfig") -> TableStructureAnalysis:
    prompt_text = """Analyze the following table data and identify its structure.

MOST tables are a SINGLE TABLE - only split if you see CLEAR evidence of merged tables.

Signs that would require splitting (ONLY split if you see these):
- A row that clearly looks like column headers appearing AFTER data rows
- Text like "Table 2:" or a completely different table title in the middle
- Column structure completely changes (different number of columns or totally different content types)

Signs of multi-row headers (common, does NOT mean multiple tables):
- First 1-3 rows contain category names, subcategories, or column groupings
- Hierarchical structure in the top rows (e.g., "Q1 2024" spanning multiple sub-columns)
- Empty cells in header rows where labels span multiple columns

DO NOT split just because:
- Data values change or there are empty rows
- There's a subtotal or category row
- The content type varies slightly

Each row is prefixed with its 0-based index in square brackets: "[0]", "[1]", etc.

Table Data:
{table_markdown}

Return ONE table entry (start_row=0) unless you see CLEAR evidence of merged tables."""

    prompt = PromptTemplate(prompt_text)

    llm, _ = llm_config.to_llama_index()
    analysis = llm.structured_predict(TableStructureAnalysis, prompt, table_markdown=table_markdown)

    _logger.debug(f"Raw LLM response: tables={analysis.tables}, reasoning={analysis.reasoning}")

    # Validate and sanitize the response
    validated_tables = []
    for segment in analysis.tables:
        validated_tables.append(
            TableSegment(
                start_row=max(0, segment.start_row),
                num_header_rows=max(1, min(4, segment.num_header_rows)),
            )
        )

    # Sort by start_row and ensure first table starts at 0
    validated_tables.sort(key=lambda t: t.start_row)
    if validated_tables and validated_tables[0].start_row != 0:
        validated_tables[0] = TableSegment(start_row=0, num_header_rows=validated_tables[0].num_header_rows)

    return TableStructureAnalysis(tables=validated_tables, reasoning=analysis.reasoning)


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
