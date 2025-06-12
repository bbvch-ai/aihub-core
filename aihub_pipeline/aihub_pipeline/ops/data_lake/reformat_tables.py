from io import StringIO

import pandas as pd
from bs4 import BeautifulSoup
from dagster import op

from aihub_pipeline.types.DocumentWithFigureInfo import DocumentWithFigureInfo


@op(code_version="v1")
def reformat_tables(
    document: DocumentWithFigureInfo,
) -> DocumentWithFigureInfo:
    """
    Convert HTML tables in the document to Markdown tables.
    """
    if not document.text_resource or not document.text_resource.text:
        return document

    soup = BeautifulSoup(document.text_resource.text, "html.parser")

    table_tags = soup.find_all("table")

    for table in table_tags:
        # TODO if table is very long split into smaller tables with copied headers
        markdown_table = pd.read_html(StringIO(str(table)))[0].fillna("").to_markdown()
        table.replace_with(f"<table>{markdown_table}</table>")

    document.text_resource.text = str(soup)

    if document.operation_id and document.figure_ids:
        del document.metadata["operation_id"]
        del document.metadata["figure_ids"]

    return document
