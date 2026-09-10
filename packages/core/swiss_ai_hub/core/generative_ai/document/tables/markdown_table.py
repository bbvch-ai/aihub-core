import logging
import re
from collections.abc import Callable
from typing import Annotated

import pandas as pd

logger = logging.getLogger(__name__)


def create_markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return df.to_markdown(index=False)

    if has_integer_column_indices(df):
        df = apply_header_rows(df.copy(), 1)

    return df.to_markdown(index=False)


def create_compact_markdown_table(df: pd.DataFrame) -> str:
    """
    Render a DataFrame as markdown without tabulate's column padding.

    `df.to_markdown()` pads every cell to the width of the widest cell in its column. On a wide table whose
    first row holds long multi-language headers that inflates the output ~36x (measured: 62KB -> 2.2MB on a
    579x10 table), which lands in the document store and every downstream buffer before anything is chunked.
    """
    if df.empty:
        return df.to_markdown(index=False)

    if has_integer_column_indices(df):
        df = apply_header_rows(df.copy(), 1)

    header = [_markdown_cell(column) for column in df.columns]
    lines = [
        _markdown_row(header),
        _markdown_row(["---"] * len(header)),
        *(_markdown_row([_markdown_cell(value) for value in row]) for row in df.values),
    ]
    return "\n".join(lines)


def _markdown_row(cells: list[str]) -> str:
    return f"| {' | '.join(cells)} |"


def _markdown_cell(value: object) -> str:
    """
    Keep every cell on one line, free of delimiters, and free of placeholder text.

    `parse_markdown_table` splits rows on a bare `|` and drops any row whose cell count then disagrees with the
    header, so a backslash escape would still cost the row its data. Substituting is the only option that keeps
    the row. Empty cells are blanked the same way `format_for_llm` does them — a merged or empty cell reaches
    here as NaN, and rendering it would embed the literal string "nan" in the indexed content.
    """
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""

    cell = str(value).replace("\r", " ").replace("\n", " ").replace("|", "/").strip()
    return "" if cell.lower() in ("none", "nan", "<na>") else cell


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
    include_header_as_data: Annotated[
        bool,
        "Whether to include the header row as data rows and use integer column indices (0, 1, 2...).",
    ] = False,
) -> pd.DataFrame | None:
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


def wrap_tables_with_tags(tables: list[str]) -> str:
    return "\n\n".join(f"<table>{t}</table>" for t in tables if t.strip())


def wrap_markdown_tables(markdown_content: str) -> str:
    """Wrap markdown tables in <table> tags so MarkdownStructuralNodeParser can identify them."""
    pattern = r"(\|[^\n]+\|\r?\n\|[:\-| ]+\|\r?(?:\n\|[^\n]+\|\r?)*)"

    tables = re.findall(pattern, markdown_content)

    for table in tables:
        wrapped = wrap_tables_with_tags([table])
        markdown_content = markdown_content.replace(table, wrapped, 1)

    return markdown_content


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
