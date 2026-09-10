import pytest

from swiss_ai_hub.core.generative_ai.document.loaders.document_loader_selector import DocumentLoaderSelector
from swiss_ai_hub.core.generative_ai.document.loaders.eml_loader import EmlLoader
from swiss_ai_hub.core.generative_ai.document.loaders.mark_it_down_loader import MarkItDownLoader
from swiss_ai_hub.core.generative_ai.document.loaders.mineru_loader import MineruLoader
from swiss_ai_hub.core.generative_ai.document.loaders.raw_loader import RawLoader


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("notes.txt", RawLoader),
        ("data.csv", RawLoader),
        ("invoice.pdf", MineruLoader),
        ("scan.jpeg", MineruLoader),
        ("cat.jpg", MineruLoader),
        ("order.docx", MarkItDownLoader),
        ("deck.pptx", MarkItDownLoader),
        ("forwarded.eml", EmlLoader),
        ("outlook.msg", MarkItDownLoader),
        ("archive.zip", type(None)),
        ("recording.wav", type(None)),
    ],
)
def test_each_supported_family_routes_to_its_own_loader(filename: str, expected: type):
    """PDFs and images are MinerU's; Office documents are MarkItDown's. Conflating the two would send a Word file to
    an OCR service that cannot read it. `.eml` is `EmlLoader`'s — see the ordering test below."""
    assert isinstance(DocumentLoaderSelector.for_file(filename), expected)


def test_the_extension_comes_from_the_content_type_when_the_filename_has_none():
    """Mail attachments are why: a part can arrive with a Content-Type and no usable filename."""
    assert DocumentLoaderSelector.extension_for("attachment", "application/pdf") == "pdf"
    assert isinstance(DocumentLoaderSelector.for_file("attachment", "application/pdf"), MineruLoader)


def test_a_content_type_with_parameters_still_resolves():
    assert DocumentLoaderSelector.extension_for("attachment", "text/plain; charset=utf-8") == "txt"


def test_the_filename_wins_over_the_content_type():
    """A sender's Content-Type is a claim; the extension is what both other call sites already trust."""
    assert DocumentLoaderSelector.extension_for("order.docx", "application/octet-stream") == "docx"


def test_an_unresolvable_file_returns_none_rather_than_raising():
    """The API turns this into a 400 and the mail agent skips the attachment — neither wants an exception here."""
    assert DocumentLoaderSelector.extension_for("noname", "") is None
    assert DocumentLoaderSelector.for_extension(None) is None
    assert DocumentLoaderSelector.for_extension("") is None


def test_the_extension_is_matched_case_insensitively_and_without_its_dot():
    assert isinstance(DocumentLoaderSelector.for_file("INVOICE.PDF"), MineruLoader)
    assert isinstance(DocumentLoaderSelector.for_extension(".pdf"), MineruLoader)


def test_the_extension_lists_are_owned_by_the_loaders():
    """A copied list would drift the moment a loader gains a format, so the selector must read theirs.

    `eml` is the one deliberate exception: MarkItDown still claims it for the ingestion pipeline and the parsing
    endpoint, which build their own maps from that list, but here it is `EmlLoader`'s — see the ordering test below.
    """
    for extension in RawLoader.SUPPORTED_EXTENSIONS:
        assert isinstance(DocumentLoaderSelector.for_extension(extension), RawLoader)
    for extension in MarkItDownLoader.SUPPORTED_EXTENSIONS:
        if extension in EmlLoader.SUPPORTED_EXTENSIONS:
            continue
        assert isinstance(DocumentLoaderSelector.for_extension(extension), MarkItDownLoader)
    for extension in EmlLoader.SUPPORTED_EXTENSIONS:
        assert isinstance(DocumentLoaderSelector.for_extension(extension), EmlLoader)


def test_eml_beats_markitdown_even_though_markitdown_still_claims_it():
    """`MarkItDownLoader.SUPPORTED_EXTENSIONS` still lists `eml`, so only the chain order keeps mail off it.

    It is left listed deliberately: the ingestion pipeline and the API's parsing endpoint build their own maps from
    that list, and this issue does not change either. What must not happen is `.eml` reaching MarkItDown *here*,
    where it would come back as the raw RFC822 source — base64 attachment payloads included — instead of markdown.
    """
    assert "eml" in MarkItDownLoader.SUPPORTED_EXTENSIONS
    assert isinstance(DocumentLoaderSelector.for_file("forwarded.eml"), EmlLoader)


def test_msg_stays_with_markitdown():
    """Outlook's binary format; the stdlib `email` module cannot read it, so `EmlLoader` must not claim it."""
    assert "msg" not in EmlLoader.SUPPORTED_EXTENSIONS
    assert isinstance(DocumentLoaderSelector.for_file("outlook.msg"), MarkItDownLoader)
