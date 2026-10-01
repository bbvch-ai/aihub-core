import unicodedata

import pytest

from swiss_ai_hub.core.generative_ai.knowledge_documents.invalid_path_pattern_error import InvalidPathPatternError
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_glob import PathGlob

pytestmark = pytest.mark.unit

_UMLAUT_NFD = unicodedata.normalize("NFD", "invoices/Prüfbericht-Ä.md")


@pytest.mark.parametrize(
    ("pattern", "path", "expected"),
    [
        ("invoices/2025/**/*.pdf", "invoices/2025/q1/acme.pdf", True),
        ("invoices/2025/**/*.pdf", "invoices/2025/x/y/z/acme.pdf", True),
        ("invoices/2025/**/*.pdf", "invoices/2025/acme.pdf", True),
        ("invoices/2025/**/*.pdf", "invoices/2024/acme.pdf", False),
        ("invoices/2025/**/*.pdf", "invoices/2025/q1/acme.pdf.txt", False),
        ("invoices/2025/**/*.pdf", "archive/invoices/2025/acme.pdf", False),
        ("invoices/2025/**", "archive/invoices/2025/acme.pdf", False),
        ("*.pdf", "acme.pdf", True),
        ("*.pdf", "invoices/acme.pdf", False),
        ("**/*.pdf", "acme.pdf", True),
        ("*.pdf", "ACME.PDF", True),
        ("Invoices/**", "invoices/2025/a.pdf", True),
        ("**/*.{pdf,docx}", "a/b.docx", True),
        ("**/*.{pdf,docx}", "a/b.pdf", True),
        ("**/*.{pdf,docx}", "a/b.md", False),
        ("{invoices,contracts}/{2024,2025}/*", "contracts/2024/x.md", True),
        ("{invoices,contracts}/{2024,2025}/*", "contracts/2023/x.md", False),
        ("a/{x,{y,z}}.md", "a/z.md", True),
        ("a/{literal}.md", "a/{literal}.md", True),
        ("invoices/Prüf*", _UMLAUT_NFD, True),
        ("acme-000?.pdf", "acme-0001.pdf", True),
        ("acme-000[12].pdf", "acme-0003.pdf", False),
        ("/invoices/*.pdf", "invoices/a.pdf", True),
        ("**", "anything/at/all.txt", True),
    ],
)
def test_matches(pattern: str, path: str, expected: bool) -> None:
    assert PathGlob(pattern).matches(path) is expected


def test_nfc_path_matches_nfd_pattern() -> None:
    assert PathGlob(_UMLAUT_NFD).matches("invoices/Prüfbericht-Ä.md")


@pytest.mark.parametrize("pattern", ["", "/"])
def test_empty_pattern_is_rejected_with_a_hint(pattern: str) -> None:
    with pytest.raises(InvalidPathPatternError, match=r"'\*\*'"):
        PathGlob(pattern)


def test_brace_explosion_is_rejected() -> None:
    with pytest.raises(InvalidPathPatternError, match="more than 64"):
        PathGlob("{a,b}" * 7)
