import logging
import re
from io import StringIO

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
            frames = pd.read_html(StringIO(f"<table>{table_content}</table>"))
        except ValueError:
            logger.warning(f"HTML table could not be parsed, leaving as-is. Preview: {table_content[:200]!r}")
            return match.group(0)

        if not frames or frames[0].empty:
            logger.warning(f"HTML table parsed to an empty frame, leaving as-is. Preview: {table_content[:200]!r}")
            return match.group(0)

        return wrap_tables_with_tags([create_compact_markdown_table(frames[0].astype(str))])
