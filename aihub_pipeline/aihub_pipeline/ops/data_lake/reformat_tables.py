import re
from io import StringIO

import pandas as pd
from dagster import OpExecutionContext, op

from aihub_pipeline.types.DocumentWithFigureInfo import DocumentWithFigureInfo
from aihub_pipeline.util.timeout_utils import timeout, RegexTimeoutError


@op(code_version="v2")
def reformat_tables(
    context: OpExecutionContext,
    document: DocumentWithFigureInfo,
) -> DocumentWithFigureInfo:
    """
    Convert HTML tables in the document to Markdown tables.
    Uses a more secure regex pattern that prevents catastrophic backtracking.
    """
    updated_content = document.text_resource.text

    table_pattern = r"<table[^>]*>[\s\S]*?<\/table>"

    MAX_REGEX_TIME = 5  # seconds

    try:
        with timeout(MAX_REGEX_TIME):
            instances = re.finditer(table_pattern, updated_content, re.DOTALL | re.IGNORECASE)
            matches = list(instances)

    except RegexTimeoutError:
        context.log.error("Regex operation timed out - potential ReDoS attack detected")
        return document
    except re.error as e:
        context.log.error(f"Regex error: {e}")
        return document

    matches.reverse()

    for match in matches:
        start, end = match.span()
        html_table = match.group(0)

        # TODO if table length will exceed VS token limit, split into smaller tables with copied headers

        try:
            markdown_table = pd.read_html(StringIO(html_table))[0].fillna("").to_markdown()
            updated_content = updated_content[:start] + "\n" + markdown_table + "\n" + updated_content[end:]

        except Exception as e:
            context.log.error(f"Failed to convert table: {e}")
            continue

    document.text_resource.text = updated_content

    if document.operation_id:
        del document.metadata["operation_id"]
        del document.metadata["figure_ids"]
    return document
