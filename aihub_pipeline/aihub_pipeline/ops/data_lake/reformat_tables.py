from io import StringIO

import pandas as pd
from bs4 import BeautifulSoup
from dagster import OpExecutionContext, op

from aihub_pipeline.types.DocumentWithFigureInfo import DocumentWithFigureInfo


@op(code_version="v1")
def reformat_tables(
    context: OpExecutionContext,
    document: DocumentWithFigureInfo,
) -> DocumentWithFigureInfo:
    """
    Convert HTML tables in the document to Markdown tables.
    Uses a more secure regex pattern that prevents catastrophic backtracking.
    """
    soup = BeautifulSoup(document.text_resource.text, "html.parser")

    table_tags = soup.find_all("table")

    for table in table_tags:
        # TODO if table is very long split into smaller tables with copied headers
        try:
            markdown_table = pd.read_html(StringIO(str(table)))[0].fillna("").to_markdown()
            table.replace_with(f"<table>{markdown_table}</table>")
        except Exception as e:
            context.log.error(f"Failed to convert table to Markdown: {str(e)}")
            continue

    document.text_resource.text = str(soup)

    if document.operation_id and document.figure_ids:
        del document.metadata["operation_id"]
        del document.metadata["figure_ids"]

    return document
