"""Table refinement using LLM to detect table structure and split merged tables."""

import logging
import re
from typing import TYPE_CHECKING

import pandas as pd

from aihub_lib.generative_ai.document.tables import create_markdown_table

if TYPE_CHECKING:
    from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig

_logger = logging.getLogger(__name__)


def refine_document_tables(markdown_text: str, llm_config: "LLMConfig") -> str:
    """Refine tables in markdown text using LLM to detect structure and split merged tables.

    Finds all markdown tables in the text and processes them with LLM to:
    - Detect multi-row headers
    - Split incorrectly merged tables
    - Properly format table structure

    Tables must already be wrapped in <table> tags (as produced by DoclingLoader).
    """
    table_pattern = r"<table>(.*?)</table>"
    matches = list(re.finditer(table_pattern, markdown_text, re.DOTALL))

    if not matches:
        _logger.debug("No <table> tags found in document")
        return markdown_text

    _logger.info(f"Refining {len(matches)} table(s) with LLM")

    result = markdown_text
    offset = 0

    for match in matches:
        table_content = match.group(1).strip()
        df = _parse_markdown_table_to_dataframe(table_content)

        if df is None or df.empty:
            _logger.debug("Could not parse table, skipping")
            continue

        refined_tables = create_markdown_table(df, llm_config)
        individual_tables = refined_tables.split("\n\n")
        wrapped_tables = "\n\n".join(f"<table>{t}</table>" for t in individual_tables if t.strip())

        start = match.start() + offset
        end = match.end() + offset
        result = result[:start] + wrapped_tables + result[end:]
        offset += len(wrapped_tables) - (end - start)

    return result


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
