import re
from io import StringIO

import pandas as pd
from dagster import OpExecutionContext

from aihub_pipeline.types.RefDocDocument import RefDocDocument


def reformat_tables(context: OpExecutionContext, document: RefDocDocument) -> RefDocDocument:
    """Convert HTML tables in the document to Markdown tables."""
    updated_content = document.text_resource.text

    table_pattern = r"<table.*?>.*?</table>"

    # Find all HTML tables in the content
    instances = re.finditer(table_pattern, updated_content, re.DOTALL)

    # We need to process matches from end to beginning to avoid index shifting
    matches = list(instances)
    matches.reverse()

    for match in matches:
        start, end = match.span()
        html_table = match.group(0)

        try:
            # TODO change nan to empty string for pandas
            # Convert the HTML table to a pandas DataFrame and then to markdown
            markdown_table = pd.read_html(StringIO(html_table))[0].to_markdown()

            # Replace the HTML table with the markdown table
            updated_content = updated_content[:start] + "\n" + markdown_table + "\n" + updated_content[end:]
        except Exception as e:
            context.log.error(f"Failed to convert table: {e}")

    document.text_resource.text = updated_content
    return document
