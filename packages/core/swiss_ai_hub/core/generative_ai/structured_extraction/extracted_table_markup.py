import re
from typing import Annotated

_START = '[aihub-extracted-table]: # "rows={rows}"'
_END = "[/aihub-extracted-table]: #"
# Whole lines only: a cell quoting a marker sits inside a table row and must not end the table early.
_MARKED = re.compile(
    r'^\[aihub-extracted-table\]: # "rows=(\d+)"[ \t]*\r?$.*?^\[/aihub-extracted-table\]: #[ \t]*(?=\r?$)',
    re.DOTALL | re.MULTILINE,
)


class ExtractedTableMarkup:
    """How an extracted table is marked in an answer, so later turns can leave it out.

    Chat clients send every earlier answer back with each new message. A table of hundreds of rows would then ride on
    every later event of the conversation and crowd the model's context, so the markers let the API, the chat pipe and
    the agents replace it with one line; the summary that follows the table stays. The markers are markdown link
    reference definitions because chat clients render nothing for them, while Open WebUI shows HTML comments as text.
    """

    @staticmethod
    def wrap(table: Annotated[str, "A markdown table"], rows: Annotated[int, "How many rows it holds"]) -> str:
        return f"{_START.format(rows=rows)}\n\n{table}\n\n{_END}"

    @staticmethod
    def condensed(text: Annotated[str, "An answer that may hold marked tables"]) -> str:
        return _MARKED.sub(lambda match: f"[A table of {match.group(1)} extracted rows was shown here.]", text)
