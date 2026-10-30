import csv
import io
from typing import Annotated

# Spreadsheet programs run a cell that starts with one of these as a formula, so a document's text could otherwise
# run code on the reader's machine once the file is opened (CSV injection).
_FORMULA_STARTS = ("=", "+", "-", "@", "\t", "\r")
# Excel reads a CSV without a byte order mark as the system's legacy encoding and garbles umlauts.
_BYTE_ORDER_MARK = "\ufeff"


class ExtractedTableCsv:
    """An extracted table as a CSV file that spreadsheet programs open safely and with the right encoding."""

    @staticmethod
    def encode(
        columns: Annotated[list[str], "The header"],
        rows: Annotated[list[list[str | float | int | bool | None]], "The rows, cells in column order"],
    ) -> bytes:
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\r\n")
        writer.writerow([ExtractedTableCsv._cell(column) for column in columns])
        writer.writerows([ExtractedTableCsv._cell(value) for value in row] for row in rows)
        return (_BYTE_ORDER_MARK + buffer.getvalue()).encode("utf-8")

    @staticmethod
    def _cell(value: str | float | int | bool | None) -> str:
        if value is None:
            return ""
        text = str(value)
        if isinstance(value, str) and text.startswith(_FORMULA_STARTS):
            return f"'{text}"
        return text
