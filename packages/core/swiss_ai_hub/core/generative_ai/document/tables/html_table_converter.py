import logging
import re
from io import StringIO
from typing import Any

import pandas as pd

from swiss_ai_hub.core.generative_ai.document.tables.markdown_table import (
    create_compact_markdown_table,
    wrap_tables_with_tags,
)

logger = logging.getLogger(__name__)

TABLE_PATTERN = re.compile(r"<table>(.*?)</table>", re.DOTALL)
HTML_ROW_PATTERN = re.compile(r"<t[rdh][\s>]", re.IGNORECASE)


class HtmlTableConverter:
    """
    Normalises HTML tables emitted by document parsers into markdown tables.

    Everything downstream of the loaders — LLM table refinement and the node parser's table chunker — reaches
    for `parse_markdown_table`, which needs a markdown separator row. MinerU emits `<table><tr><td>` for every
    table it recognises, so without this step those tables are detected but never parsed: refinement skips them
    and the chunker emits each one as a single unbounded node. Converting here keeps that contract in one place,
    the way `DoclingLoader.convert_tables_to_markdown` used to.

    Every cell is kept as written: pandas would otherwise read `1,00` as one hundred (its thousands separator is a
    comma), drop the zeros of `0.10` and `0042`, and turn `NA` into a blank.
    """

    @staticmethod
    def convert(markdown_content: str) -> str:
        return TABLE_PATTERN.sub(HtmlTableConverter._convert_match, markdown_content)

    @staticmethod
    def _convert_match(match: re.Match[str]) -> str:
        table_content = match.group(1).strip()

        if not HTML_ROW_PATTERN.search(table_content):
            return match.group(0)

        try:
            frames = HtmlTableConverter._read_as_text(f"<table>{table_content}</table>")
        except ValueError:
            logger.warning(f"HTML table could not be parsed, leaving as-is. Preview: {table_content[:200]!r}")
            return match.group(0)

        if not frames or frames[0].empty:
            logger.warning(f"HTML table parsed to an empty frame, leaving as-is. Preview: {table_content[:200]!r}")
            return match.group(0)

        return wrap_tables_with_tags([create_compact_markdown_table(frames[0].astype(str))])

    @staticmethod
    def _read_as_text(html: str) -> list[pd.DataFrame]:
        """The tables with every cell as its text. A converter keyed past the last column fails the parse, so the
        first pass only measures the width."""
        options: dict[str, Any] = {"thousands": None, "keep_default_na": False}
        frames = pd.read_html(StringIO(html), **options)
        if not frames:
            return frames
        width = frames[0].shape[1]
        return pd.read_html(StringIO(html), converters=dict.fromkeys(range(width), str), **options)
