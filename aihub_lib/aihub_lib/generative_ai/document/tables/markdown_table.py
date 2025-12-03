import logging
import re
from collections.abc import Callable

import pandas as pd

logger = logging.getLogger(__name__)


def create_markdown_table(df: pd.DataFrame) -> str:
    """
    Convert a DataFrame to a markdown table string.

    Used by DoclingLoader to convert tables without LLM refinement.
    If the DataFrame has integer column indices, assumes the first row contains headers.
    """
    if df.empty:
        return df.to_markdown(index=False)

    if has_integer_column_indices(df):
        df = apply_header_rows(df.copy(), 1)

    return df.to_markdown(index=False)


def has_integer_column_indices(df: pd.DataFrame) -> bool:
    return all(isinstance(col, int) for col in df.columns)


def apply_header_rows(df: pd.DataFrame, num_header_rows: int) -> pd.DataFrame:
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


def parse_markdown_table(
    markdown_table: str,
    include_header_as_data: bool = False,
) -> pd.DataFrame | None:
    """
    Parse a markdown table string into a DataFrame.

    If include_header_as_data is True, the header row becomes the first data row
    and columns are integer indices (0, 1, 2...). Used for LLM analysis where
    the LLM determines which rows are headers.
    """
    try:
        lines = markdown_table.strip().split("\n")
        if len(lines) < 2:
            return None

        header_line = lines[0]

        # Find separator line (handles alignment markers like :---, :---:, ---:)
        separator_idx = None
        for i, line in enumerate(lines[1:], 1):
            if re.match(r"^\|[\s:\-|]+\|$", line.strip()):
                separator_idx = i
                break

        if separator_idx is None:
            return None

        data_lines = lines[separator_idx + 1 :] if len(lines) > separator_idx + 1 else []
        headers = [col.strip() for col in header_line.split("|")[1:-1]]
        num_cols = len(headers)

        if not headers:
            return None

        # Parse data rows
        data_rows: list[list[str]] = []
        for line in data_lines:
            row = [cell.strip() for cell in line.split("|")[1:-1]]
            if len(row) == num_cols:
                data_rows.append(row)

        if include_header_as_data:
            # Header becomes first data row, columns are integers
            all_rows = [headers] + data_rows
            return pd.DataFrame(all_rows, columns=list(range(num_cols)))
        else:
            # Header becomes column names
            return pd.DataFrame(data_rows, columns=headers)

    except (ValueError, IndexError, KeyError) as e:
        logger.debug(f"Failed to parse markdown table: {e}")
        return None


def format_for_llm(df: pd.DataFrame) -> str:
    """
    Format DataFrame as indexed text for LLM analysis.

    Each row is prefixed with its 0-based index:
    [0] col1_value | col2_value | col3_value
    [1] col1_value | col2_value | col3_value

    Empty cells (None, NaN, "nan", "none", "<na>") are represented as empty strings.
    """

    def format_cell(value: object) -> str:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return ""
        str_value = str(value).strip()
        if str_value.lower() in ("none", "nan", "<na>"):
            return ""
        return str_value

    lines = []
    for idx, row in enumerate(df.values):
        row_values = " | ".join(format_cell(v) for v in row)
        lines.append(f"[{idx}] {row_values}")
    return "\n".join(lines)


def split_dataframe_into_chunks(
    df: pd.DataFrame,
    max_tokens: int,
    token_counter: Callable[[str], int],
) -> list[str]:
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
