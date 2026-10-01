import time
import unicodedata

import pytest

from swiss_ai_hub.core.generative_ai.knowledge_documents.invalid_path_pattern_error import InvalidPathPatternError
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_regex import PathRegex

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("pattern", "path", "expected"),
    [
        ("acme", "invoices/2025/q1/acme-0001.pdf", True),
        ("^acme", "invoices/2025/q1/acme-0001.pdf", False),
        (r"^invoices/2025/.*\.pdf$", "invoices/2025/q1/acme.pdf", True),
        (r"^invoices/2025/.*\.pdf$", "invoices/2025/q1/acme.PDF", False),
        (r"(?i)^invoices/2025/.*\.pdf$", "invoices/2025/q1/acme.PDF", True),
        (r"20(24|25)/", "invoices/2024/a.pdf", True),
        ("Prüf", unicodedata.normalize("NFD", "invoices/Prüfbericht.md"), True),
    ],
)
def test_searches_anywhere_in_the_path(pattern: str, path: str, expected: bool) -> None:
    assert PathRegex(pattern).matches(path) is expected


def test_invalid_regex_is_rejected_with_a_hint() -> None:
    with pytest.raises(InvalidPathPatternError, match="escape literal characters") as raised:
        PathRegex("invoices/(2025")
    assert raised.value.pattern == "invoices/(2025"


def test_overlong_pattern_is_rejected() -> None:
    with pytest.raises(InvalidPathPatternError, match="longer than 500"):
        PathRegex("a" * 501)


def test_pattern_that_breaks_the_standard_library_returns_promptly() -> None:
    """`re` was still running after 20 s on this pattern and path; the `regex` engine answers at once."""
    started = time.monotonic()
    assert PathRegex(r"^(\w+\w?)+$").matches("a" * 26 + "!") is False
    assert time.monotonic() - started < 1


def test_catastrophic_pattern_times_out_with_a_hint() -> None:
    catastrophic = PathRegex(r"^(a|a)*$")
    started = time.monotonic()
    with pytest.raises(InvalidPathPatternError, match="too long to match"):
        catastrophic.matches("a" * 40 + "b")
    assert time.monotonic() - started < 1


def test_budget_covers_the_whole_call_not_each_path() -> None:
    """About 40 ms per path stays under any per-path timeout, but across 300 paths it blocked for about 13 s."""
    slow_per_path = PathRegex(r"^(a|a)*$")
    paths = ["a" * 18 + "b"] * 300
    started = time.monotonic()
    with pytest.raises(InvalidPathPatternError, match="too long to match"):
        slow_per_path.matches_all(paths)
    assert time.monotonic() - started < 1.5


def test_matches_all_keeps_order() -> None:
    assert PathRegex("acme").matches_all(["a/acme.pdf", "b/globex.pdf", "acme.md"]) == [True, False, True]
