import csv
import io

import pytest

from swiss_ai_hub.core.generative_ai.structured_extraction.extracted_table_csv import ExtractedTableCsv

pytestmark = pytest.mark.unit

BYTE_ORDER_MARK = "﻿".encode()


def _parsed(body: bytes) -> list[list[str]]:
    return list(csv.reader(io.StringIO(body.decode("utf-8-sig"), newline="")))


def test_the_file_starts_with_a_byte_order_mark_so_spreadsheets_read_umlauts():
    body = ExtractedTableCsv.encode(["Lieferant"], [["Müller AG"]])

    assert body.startswith(BYTE_ORDER_MARK)
    assert body.count(BYTE_ORDER_MARK) == 1
    assert "Müller AG".encode() in body


def test_lines_end_with_crlf():
    body = ExtractedTableCsv.encode(["a", "b"], [["1", "2"], ["3", "4"]])

    assert body[len(BYTE_ORDER_MARK) :] == b"a,b\r\n1,2\r\n3,4\r\n"


def test_commas_quotes_and_line_breaks_stay_inside_their_cell():
    rows = [['Rack, 19"', 'He said "go"', "line one\nline two", "x\r\ny"]]

    body = ExtractedTableCsv.encode(["a", "b", "c", "d"], rows)

    assert _parsed(body) == [["a", "b", "c", "d"], rows[0]]
    assert b'"Rack, 19"""' in body


@pytest.mark.parametrize("start", ["=", "+", "-", "@", "\t", "\r"])
def test_a_text_cell_a_spreadsheet_would_run_as_a_formula_is_prefixed(start: str):
    body = ExtractedTableCsv.encode(["a"], [[f"{start}HYPERLINK(1)"]])

    assert _parsed(body)[1] == [f"'{start}HYPERLINK(1)"]


def test_the_header_is_guarded_like_the_cells():
    body = ExtractedTableCsv.encode(["=cmd", "Amount"], [])

    assert _parsed(body) == [["'=cmd", "Amount"]]


def test_numbers_and_booleans_are_written_untouched():
    body = ExtractedTableCsv.encode(["a", "b", "c", "d"], [[-5, -1.25, True, 0]])

    assert _parsed(body)[1] == ["-5", "-1.25", "True", "0"]


def test_an_empty_value_is_an_empty_cell():
    body = ExtractedTableCsv.encode(["a", "b", "c"], [[None, "", "x"]])

    assert _parsed(body)[1] == ["", "", "x"]


def test_a_cell_starting_with_an_ordinary_character_is_unchanged():
    body = ExtractedTableCsv.encode(["a"], [["a=b", "100 - 5"]])

    assert _parsed(body)[1] == ["a=b", "100 - 5"]
