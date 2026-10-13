import datetime
import io
import re
import tracemalloc
import zipfile

import pytest
from openpyxl import Workbook

from swiss_ai_hub.core.generative_ai.document.loaders.xlsx_markdown_converter import XlsxMarkdownConverter
from swiss_ai_hub.core.generative_ai.document.tables.markdown_table import parse_markdown_table, wrap_markdown_tables


def workbook(*sheets: tuple[str, list[list[object]]]) -> bytes:
    book = Workbook()
    book.remove(book.active)
    for title, rows in sheets:
        sheet = book.create_sheet(title)
        for row in rows:
            sheet.append(row)
    buffer = io.BytesIO()
    book.save(buffer)
    return buffer.getvalue()


def convert(*sheets: tuple[str, list[list[object]]]) -> str:
    return XlsxMarkdownConverter.convert(workbook(*sheets))


def table_lines(markdown: str) -> list[str]:
    return [line for line in markdown.splitlines() if line.startswith("|")]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (42.31, "42.31"),
        (1234567.891, "1234567.891"),
        (1.2345e-05, "1.2345e-05"),
        (1e21, "1e+21"),
        (0.1 + 0.2, "0.3"),
        (-1 / 9, "-0.111111111111111"),
        (3, "3"),
        (True, "TRUE"),
        (False, "FALSE"),
        (datetime.date(2025, 5, 4), "2025-05-04"),
        (datetime.datetime(2025, 5, 4, 13, 30), "2025-05-04 13:30:00"),
        (datetime.time(9, 15), "09:15:00"),
        ("text", "text"),
    ],
)
def test_a_value_is_rendered_as_entered(value: object, expected: str):
    markdown = convert(("Data", [["value"], [value]]))

    assert table_lines(markdown)[-1] == f"| {expected} |"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (datetime.datetime(2013, 8, 20, 15, 30, 17, 999000), "2013-08-20 15:30:18"),
        (datetime.datetime(2025, 5, 4, 23, 59, 59, 999500), "2025-05-05"),
        (datetime.datetime(2025, 5, 4, 13, 30, 0, 250000), "2025-05-04 13:30:00.250000"),
        (datetime.time(15, 30, 17, 999000), "15:30:18"),
    ],
)
def test_a_time_reads_back_to_the_entered_second(value: object, expected: str):
    """Excel's day fractions read back a millisecond short of the second that was entered."""
    markdown = convert(("Data", [["value"], [value]]))

    assert table_lines(markdown)[-1] == f"| {expected} |"


def test_a_sheet_is_a_heading_and_a_table_headed_by_its_first_row():
    markdown = convert(("Orders", [["id", "amount"], [1, 42.31], [2, 0.15]]))

    assert markdown == "## Orders\n| id | amount |\n| --- | --- |\n| 1 | 42.31 |\n| 2 | 0.15 |"


def test_an_empty_cell_is_blank_rather_than_nan():
    markdown = convert(("Data", [["a", "b", "c"], [1, None, 3]]))

    assert table_lines(markdown)[-1] == "| 1 |  | 3 |"


def test_text_that_reads_like_a_pandas_placeholder_is_kept():
    markdown = convert(("People", [["name", "allergies", "code"], ["Nan", "None", "<NA>"], ["Ann", "nan", "NaN"]]))

    assert table_lines(markdown)[2:] == ["| Nan | None | <NA> |", "| Ann | nan | NaN |"]


def test_delimiters_in_a_cell_cannot_break_its_row():
    markdown = convert(("Data", [["note"], ["a|b"], ["line1\nline2"]]))

    assert table_lines(markdown)[2:] == ["| a/b |", "| line1 line2 |"]


def test_rows_are_padded_to_the_widest():
    markdown = convert(("Data", [["a", "b"], [1], [1, 2, 3]]))

    assert table_lines(markdown) == ["| a | b |  |", "| --- | --- | --- |", "| 1 |  |  |", "| 1 | 2 | 3 |"]


def test_empty_rows_around_the_data_are_dropped_and_a_run_between_kept_as_one():
    rows = [[], [None], ["Employee"], ["Ann"], [], [None], ["Dept"], ["HR"], [], []]

    markdown = convert(("Two Tables", rows))

    assert table_lines(markdown) == ["| Employee |", "| --- |", "| Ann |", "|  |", "| Dept |", "| HR |"]


def test_a_column_empty_in_every_row_is_dropped():
    markdown = convert(("Data", [[None, "a", None, "b"], [None, 1, None, 2]]))

    assert table_lines(markdown) == ["| a | b |", "| --- | --- |", "| 1 | 2 |"]


def test_stray_far_away_cells_cannot_blow_the_output_up():
    """One cell in the last column and one 100,000 rows down used to pad the table to 16,384 columns and add the rows
    between as empty lines."""
    book = Workbook()
    book.active.append(["id", "name"])
    book.active.append([1, "a"])
    book.active["XFD3"] = "stray"
    book.active["A100000"] = "note"
    buffer = io.BytesIO()
    book.save(buffer)

    markdown = XlsxMarkdownConverter.convert(buffer.getvalue())

    assert table_lines(markdown) == [
        "| id | name |  |",
        "| --- | --- | --- |",
        "| 1 | a |  |",
        "|  |  | stray |",
        "|  |  |  |",
        "| note |  |  |",
    ]


def test_a_sheet_declaring_a_wrong_size_is_read_whole():
    """Tools other than Excel can declare `A1:A1` for a full sheet, which the read-only reader would trust."""
    misdeclared = io.BytesIO()
    with (
        zipfile.ZipFile(io.BytesIO(workbook(("Data", [["id", "amount"], [1, 42.31], [2, 0.15]])))) as source,
        zipfile.ZipFile(misdeclared, "w") as target,
    ):
        for item in source.infolist():
            content = source.read(item.filename)
            if item.filename == "xl/worksheets/sheet1.xml":
                content = re.sub(rb'<dimension ref="[^"]+"', b'<dimension ref="A1:A1"', content)
            target.writestr(item, content)

    markdown = XlsxMarkdownConverter.convert(misdeclared.getvalue())

    assert table_lines(markdown) == ["| id | amount |", "| --- | --- |", "| 1 | 42.31 |", "| 2 | 0.15 |"]


def test_sheets_keep_their_order_and_an_empty_one_is_its_heading():
    markdown = convert(("First", [["x"], [1]]), ("Empty", []), ("Last", [["y"], [2]]))

    assert markdown.split("\n\n") == [
        "## First\n| x |\n| --- |\n| 1 |",
        "## Empty",
        "## Last\n| y |\n| --- |\n| 2 |",
    ]


def test_every_row_survives_the_table_parser():
    rows = [["id", "note", "amount"], *([index, f"row {index} | with pipe", index * 1.5] for index in range(50))]

    wrapped = wrap_markdown_tables(convert(("Data", rows)))
    table = wrapped[wrapped.index("<table>") + len("<table>") : wrapped.index("</table>")]

    parsed = parse_markdown_table(table)
    assert parsed is not None
    assert len(parsed) == 50


@pytest.mark.slow
def test_a_large_sheet_converts_in_little_memory():
    """MarkItDown needed ~950 MB for 60,000 rows of nine columns; streaming keeps it to the text's own size."""
    rows = [
        ["order_id", "order_date", "customer_id", "product_id", "quantity", "unit_price", "discount", "revenue"],
        *(
            [f"O{index:06d}", datetime.date(2025, 1, 1), f"C{index % 5000:05d}", "P0001", 3, 42.31, 0.15, 107.89]
            for index in range(60_000)
        ),
    ]
    file_bytes = workbook(("orders", rows))

    tracemalloc.start()
    try:
        markdown = XlsxMarkdownConverter.convert(file_bytes)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    assert len(table_lines(markdown)) == 60_002
    assert peak < 100 * 2**20
