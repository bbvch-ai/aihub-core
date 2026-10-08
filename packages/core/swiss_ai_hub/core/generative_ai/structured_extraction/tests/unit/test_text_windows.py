import pytest

from swiss_ai_hub.core.generative_ai.structured_extraction.text_windows import TextWindows

pytestmark = pytest.mark.unit


def _words(text: str) -> list[str]:
    return text.split()


def _document(lines: int) -> str:
    return "\n\n".join(f"Position {n}: hardware item costs {n * 100} CHF." for n in range(1, lines + 1))


def test_blank_text_has_no_windows() -> None:
    assert TextWindows.split("  \n ", 100, 10, _words) == []


def test_text_within_the_budget_is_one_unchanged_window() -> None:
    text = _document(3)

    assert TextWindows.split(text, 100, 10, _words) == [text]


def test_long_text_is_split_into_windows_within_the_budget() -> None:
    windows = TextWindows.split(_document(200), 120, 20, _words)

    assert len(windows) > 1
    assert all(len(_words(window)) <= 120 for window in windows)


def test_every_line_including_the_last_lands_in_a_window() -> None:
    windows = TextWindows.split(_document(200), 120, 20, _words)
    joined = "\n".join(windows)

    assert all(f"Position {n}:" in joined for n in range(1, 201))
    assert "Position 200: hardware item costs 20000 CHF." in windows[-1]


def test_adjacent_windows_share_text() -> None:
    windows = TextWindows.split(_document(200), 120, 20, _words)

    for previous, following in zip(windows, windows[1:], strict=False):
        assert set(previous.split("\n\n")) & set(following.split("\n\n"))


def _markdown_table(rows: int) -> str:
    """A table as MinerU renders one: single line breaks, and amounts whose decimal point reads as a sentence end."""
    header = "| Pos | Description | Amount | Currency |\n|---|---|---|---|"
    lines = [f"| {n} | External SSD 2 TB | {n * 3}.50 | CHF |" for n in range(1, rows + 1)]
    return "\n".join([header, *lines])


def test_markdown_table_rows_are_never_cut_at_a_window_edge() -> None:
    """A cut row reads as a different record, an amount of 1156 instead of 1156.50, which the merger keeps twice."""
    table = _markdown_table(200)

    windows = TextWindows.split(table, 120, 20, _words)

    assert len(windows) > 1
    assert all(line in table.splitlines() for window in windows for line in window.splitlines())


def test_markdown_table_windows_overlap_by_whole_rows() -> None:
    windows = TextWindows.split(_markdown_table(200), 120, 20, _words)

    for previous, following in zip(windows, windows[1:], strict=False):
        assert set(previous.splitlines()) & set(following.splitlines())
