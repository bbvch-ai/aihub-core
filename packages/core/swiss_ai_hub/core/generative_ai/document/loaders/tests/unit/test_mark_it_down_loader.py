import io
import struct
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import fsspec
import pytest
from botocore.exceptions import ClientError, EndpointConnectionError
from fsspec.implementations.memory import MemoryFileSystem
from llama_index.core.schema import Document
from openpyxl import Workbook
from PIL import Image
from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE
from pptx.opc.package import Part
from pptx.opc.packuri import PackURI
from pptx.oxml.ns import qn
from pptx.util import Inches

from swiss_ai_hub.core.generative_ai.document.loaders.mark_it_down_loader import MarkItDownLoader
from swiss_ai_hub.core.generative_ai.document.loaders.mark_it_down_parse_cache import MarkItDownParseCache
from swiss_ai_hub.core.generative_ai.document.loaders.parse_cache_bucket import ParseCacheBucket

DOCX_BYTES = b"docx-bytes"
IMAGE = "data:image/png;base64,iVBORw0KGgo="
SECRET = "The secret test word is PINEAPPLE."
SVG = b'<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><rect width="10" height="10"/></svg>'
SVG_BLIP_EXTENSION = "{96DAC541-7B7A-43D3-8B79-37D633B846F1}"
SVG_BLIP = "{http://schemas.microsoft.com/office/drawing/2016/SVG/main}svgBlip"
EMF = (
    struct.pack("<II", 1, 108)
    + struct.pack("<iiii", 0, 0, 99, 99)
    + struct.pack("<iiii", 0, 0, 2646, 2646)
    + b" EMF"
    + struct.pack("<IIIHHIIIiiii", 0x10000, 108, 1, 1, 0, 0, 0, 0, 1920, 1080, 508, 286)
)


@pytest.fixture(autouse=True)
def in_memory_parse_cache(monkeypatch: pytest.MonkeyPatch) -> dict[str, bytes]:
    store: dict[str, bytes] = {}
    monkeypatch.setattr(ParseCacheBucket, "read", lambda self, key: store.get(key))
    monkeypatch.setattr(
        ParseCacheBucket, "write", lambda self, key, content, content_type: store.__setitem__(key, content)
    )
    return store


@pytest.fixture
def markitdown() -> MagicMock:
    return MagicMock(convert=MagicMock(return_value=SimpleNamespace(text_content=f"# Order\n\n![chart]({IMAGE})")))


@pytest.fixture
def loader(markitdown: MagicMock, monkeypatch: pytest.MonkeyPatch) -> MarkItDownLoader:
    loader = MarkItDownLoader()
    monkeypatch.setattr(loader, "_get_converter", lambda: markitdown)
    return loader


@pytest.fixture
def memory_fs() -> Iterator[MemoryFileSystem]:
    fs = fsspec.filesystem("memory")
    yield fs
    fs.store.clear()
    fs.pseudo_dirs[:] = [""]


def png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(buffer, "PNG")
    return buffer.getvalue()


def deck(picture: str) -> bytes:
    """
    A one-slide deck whose picture is `embedded` (a PNG), `linked` (r:link, no image in the deck, also without
    `descr`), `svg` (an SVG without the PNG fallback PowerPoint usually writes) or `emf`.
    """
    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[5])
    slide.shapes.title.text = "Quarterly figures"
    slide.shapes.add_textbox(Inches(1), Inches(1), Inches(4), Inches(1)).text_frame.text = SECRET
    shape = slide.shapes.add_picture(io.BytesIO(png_bytes()), Inches(1), Inches(2))
    shape._element._nvXxPr.cNvPr.set("descr", "company logo")
    blip = shape._element.blipFill.find(qn("a:blip"))
    match picture:
        case "linked" | "linked_without_descr":
            if picture == "linked_without_descr":
                del shape._element._nvXxPr.cNvPr.attrib["descr"]
            del blip.attrib[qn("r:embed")]
            link = slide.part.relate_to("file:///C:/logo.png", RELATIONSHIP_TYPE.IMAGE, is_external=True)
            blip.set(qn("r:link"), link)
        case "svg":
            part = Part(PackURI("/ppt/media/image99.svg"), "image/svg+xml", slide.part.package, SVG)
            del blip.attrib[qn("r:embed")]
            extensions = blip.makeelement(qn("a:extLst"), {})
            extension = extensions.makeelement(qn("a:ext"), {"uri": SVG_BLIP_EXTENSION})
            extension.append(
                extension.makeelement(SVG_BLIP, {qn("r:embed"): slide.part.relate_to(part, RELATIONSHIP_TYPE.IMAGE)})
            )
            extensions.append(extension)
            blip.append(extensions)
        case "emf":
            part = Part(PackURI("/ppt/media/image98.emf"), "image/x-emf", slide.part.package, EMF)
            blip.set(qn("r:embed"), slide.part.relate_to(part, RELATIONSHIP_TYPE.IMAGE))
    buffer = io.BytesIO()
    presentation.save(buffer)
    return buffer.getvalue()


async def load_deck(mode: str, content: bytes, fs: MemoryFileSystem) -> list[Document]:
    loader = MarkItDownLoader()
    match mode:
        case "api_s3":
            return await loader.aload_data_from_bytes(content, "deck.pptx", fs=fs)
        case "api_base64":
            return await loader.aload_data_from_bytes(content, "deck.pptx", embed_base64=True)
        case "pipeline":
            fs.pipe_file("/lake/docs/deck.pptx", content)
            return await loader.aload_data("/lake/docs/deck.pptx", fs=fs)
        case "without_images":
            return await loader.aload_data_from_bytes(content, "deck.pptx", include_images=False)
    raise ValueError(mode)


def xlsx_bytes() -> bytes:
    book = Workbook()
    book.active.append(["id", "amount"])
    book.active.append([1, 42.31])
    buffer = io.BytesIO()
    book.save(buffer)
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_an_xlsx_is_streamed_without_markitdown(loader: MarkItDownLoader, markitdown: MagicMock):
    documents = await loader.aload_data_from_bytes(xlsx_bytes(), "orders.xlsx", include_images=False)

    assert "| 1 | 42.31 |" in documents[0].text
    markitdown.convert.assert_not_called()


@pytest.mark.asyncio
async def test_other_office_documents_still_go_through_markitdown(loader: MarkItDownLoader, markitdown: MagicMock):
    documents = await loader.aload_data_from_bytes(DOCX_BYTES, "order.docx", include_images=False)

    assert documents[0].text.startswith("# Order")
    markitdown.convert.assert_called_once()


@pytest.mark.asyncio
async def test_a_document_is_converted_once(
    loader: MarkItDownLoader, markitdown: MagicMock, in_memory_parse_cache: dict[str, bytes]
):
    first = await loader.aload_data_from_bytes(DOCX_BYTES, "order.docx", include_images=False)
    second = await MarkItDownLoader().aload_data_from_bytes(DOCX_BYTES, "copy.docx", include_images=False)

    assert second[0].text == first[0].text
    markitdown.convert.assert_called_once()
    assert list(in_memory_parse_cache) == [loader.parse_cache.object_key(DOCX_BYTES, "order.docx")]


@pytest.mark.asyncio
async def test_one_entry_serves_callers_with_and_without_images(loader: MarkItDownLoader, markitdown: MagicMock):
    without_images = await loader.aload_data_from_bytes(DOCX_BYTES, "order.docx", include_images=False)
    with_images = await loader.aload_data_from_bytes(DOCX_BYTES, "order.docx", embed_base64=True)

    assert "data:image" not in without_images[0].text
    assert "[image: chart]" in without_images[0].text
    assert "image/png" in with_images[0].text
    markitdown.convert.assert_called_once()


@pytest.mark.asyncio
async def test_a_reader_without_images_gets_the_text_instead_of_base64(loader: MarkItDownLoader, tmp_path: Path):
    stored = tmp_path / "order.docx"
    stored.write_bytes(DOCX_BYTES)

    documents = await loader.aload_data(str(stored), include_images=False)

    assert documents[0].text == "# Order\n\n[image: chart]"


@pytest.mark.asyncio
async def test_ingestion_reads_what_an_upload_converted(
    loader: MarkItDownLoader, markitdown: MagicMock, tmp_path: Path
):
    stored = tmp_path / "order.docx"
    stored.write_bytes(DOCX_BYTES)

    await loader.aload_data_from_bytes(DOCX_BYTES, "upload.docx", include_images=False)
    documents = await loader.aload_data(str(stored), include_images=False)

    assert documents[0].text.startswith("# Order")
    markitdown.convert.assert_called_once()


@pytest.mark.asyncio
async def test_a_failed_conversion_is_not_cached(
    loader: MarkItDownLoader, markitdown: MagicMock, in_memory_parse_cache: dict[str, bytes]
):
    markitdown.convert.side_effect = ValueError("corrupt document")

    with pytest.raises(ValueError, match="corrupt document"):
        await loader.aload_data_from_bytes(DOCX_BYTES, "order.docx", include_images=False)

    assert in_memory_parse_cache == {}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "storage_error",
    [
        EndpointConnectionError(endpoint_url="http://seaweedfs-s3:8333"),
        ClientError({"Error": {"Code": "NoSuchBucket"}}, "GetObject"),
    ],
)
async def test_a_document_still_converts_when_the_cache_cannot_be_reached(
    loader: MarkItDownLoader, markitdown: MagicMock, monkeypatch: pytest.MonkeyPatch, storage_error: Exception
):
    def unreachable(*args: object) -> None:
        raise storage_error

    monkeypatch.setattr(ParseCacheBucket, "read", unreachable)
    monkeypatch.setattr(ParseCacheBucket, "write", unreachable)

    documents = await loader.aload_data_from_bytes(DOCX_BYTES, "order.docx", include_images=False)

    assert documents[0].text.startswith("# Order")
    markitdown.convert.assert_called_once()


@pytest.mark.asyncio
async def test_an_email_body_is_converted_without_the_cache(
    loader: MarkItDownLoader, markitdown: MagicMock, in_memory_parse_cache: dict[str, bytes]
):
    await loader.aload_data_from_bytes(b"<p>Hello</p>", "body.html", include_images=False)
    await loader.aload_data_from_bytes(b"<p>Hello</p>", "body.html", include_images=False)

    assert markitdown.convert.call_count == 2
    assert in_memory_parse_cache == {}


def test_the_key_depends_on_the_bytes_and_the_extension():
    cache = MarkItDownParseCache()

    key = cache.object_key(DOCX_BYTES, "a.docx")

    assert key.startswith(f"markitdown/{cache.settings_fingerprint()}/")
    assert key.endswith(".docx/markdown.md")
    assert key == cache.object_key(DOCX_BYTES, "another name.DOCX")
    assert key != cache.object_key(DOCX_BYTES, "a.pptx")
    assert key != cache.object_key(b"other bytes", "a.docx")


def test_a_change_to_the_xlsx_rendering_starts_fresh(monkeypatch: pytest.MonkeyPatch):
    fingerprint = MarkItDownParseCache.settings_fingerprint()

    monkeypatch.setattr(MarkItDownParseCache, "XLSX_FORMAT", MarkItDownParseCache.XLSX_FORMAT + 1)

    assert MarkItDownParseCache.settings_fingerprint() != fingerprint


def test_a_new_markitdown_release_starts_fresh(monkeypatch: pytest.MonkeyPatch):
    fingerprint = MarkItDownParseCache.settings_fingerprint()

    monkeypatch.setattr(
        "swiss_ai_hub.core.generative_ai.document.loaders.mark_it_down_parse_cache.importlib.metadata.version",
        lambda name: "99.0.0",
    )

    assert MarkItDownParseCache.settings_fingerprint() != fingerprint


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["api_s3", "api_base64", "pipeline", "without_images"])
@pytest.mark.parametrize("picture", ["linked", "svg", "emf"])
async def test_a_deck_whose_picture_cannot_be_kept_still_loads(mode: str, picture: str, memory_fs: MemoryFileSystem):
    documents = await load_deck(mode, deck(picture), memory_fs)

    text = documents[0].text
    assert SECRET in text
    assert "[image: company logo]" in text
    assert ".jpg)" not in text
    assert "svg+xml" not in text
    assert "x-wmf" not in text
    assert "x-emf" not in text
    assert not [path for path in memory_fs.find("/") if "__figures__" in path]


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["api_s3", "pipeline"])
async def test_an_embedded_picture_is_still_stored_as_a_figure(mode: str, memory_fs: MemoryFileSystem):
    documents = await load_deck(mode, deck("embedded"), memory_fs)

    assert SECRET in documents[0].text
    assert "<figure>![Figure 1](s3://" in documents[0].text
    assert [path for path in memory_fs.find("/") if "__figures__" in path and path.endswith(".png")]


@pytest.mark.asyncio
async def test_a_linked_picture_without_a_description_is_named_after_its_shape(memory_fs: MemoryFileSystem):
    documents = await load_deck("api_s3", deck("linked_without_descr"), memory_fs)

    assert "[image: Picture " in documents[0].text
    assert ".jpg)" not in documents[0].text


@pytest.mark.parametrize(
    ("markdown", "expected"),
    [
        ("![logo](Picture2.jpg)", "[image: logo]"),
        ("![](Picture2.jpg)", "[image]"),
        ("![](.jpg)", "[image]"),
        ("![diagram](arch.png)", "![diagram](arch.png)"),
        (f"![x]({IMAGE})", f"![x]({IMAGE})"),
        ("![x](https://a/b.jpg)", "![x](https://a/b.jpg)"),
    ],
)
def test_only_markitdowns_name_for_an_unembedded_picture_is_marked(markdown: str, expected: str):
    assert MarkItDownLoader._mark_unembedded_pictures(markdown) == expected


@pytest.mark.asyncio
async def test_unembedded_pictures_are_marked_in_decks_only_and_after_the_cache(
    loader: MarkItDownLoader, markitdown: MagicMock, in_memory_parse_cache: dict[str, bytes]
):
    markitdown.convert.return_value = SimpleNamespace(text_content="# Slide\n\n![x](Picture2.jpg)")

    word = await loader.aload_data_from_bytes(b"word", "a.docx", include_images=False)
    deck_documents = await loader.aload_data_from_bytes(b"deck", "a.pptx", include_images=False)

    assert word[0].text == "# Slide\n\n![x](Picture2.jpg)"
    assert deck_documents[0].text == "# Slide\n\n[image: x]"
    assert in_memory_parse_cache[loader.parse_cache.object_key(b"deck", "a.pptx")] == b"# Slide\n\n![x](Picture2.jpg)"
