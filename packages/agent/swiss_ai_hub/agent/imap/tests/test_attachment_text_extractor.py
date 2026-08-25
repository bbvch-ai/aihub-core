from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from swiss_ai_hub.core.events.agent import MailAttachmentRef
from swiss_ai_hub.core.imap import DraftEmailSettings

from swiss_ai_hub.agent.imap.attachment_text_extractor import AttachmentTextExtractor
from swiss_ai_hub.agent.imap.extracted_attachment import AttachmentOutcome
from swiss_ai_hub.agent.imap.tests.mail_doubles import LOAD_ATTACHMENT, LOADER_FOR_FILE

_FILE_ID = "0d5f7a1c-3b2e-4c8d-9a6f-1e2d3c4b5a6f"
_OTHER_FILE_ID = "1a2b3c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d"


def _ref(filename: str, size_bytes: int, content_type: str = "application/pdf", file_id: str = _FILE_ID):
    return MailAttachmentRef(filename=filename, content_type=content_type, file_id=file_id, size_bytes=size_bytes)


def _settings(**overrides) -> DraftEmailSettings:
    return DraftEmailSettings(enable_draft=True, include_attachments=True, **overrides)


def _loader(text: str) -> SimpleNamespace:
    return SimpleNamespace(aload_data_from_bytes=AsyncMock(return_value=[SimpleNamespace(text=text)]))


_DEFAULT_LOADER = object()


async def _extract(refs: list[MailAttachmentRef], draft: DraftEmailSettings, loader=_DEFAULT_LOADER, load=None):
    """`loader=None` means the selector found nothing that can read the file — distinct from not overriding it."""
    resolved = _loader("Invoice total 42.00") if loader is _DEFAULT_LOADER else loader
    with (
        patch(LOAD_ATTACHMENT, new=load or AsyncMock(return_value=b"bytes")),
        patch(LOADER_FOR_FILE, return_value=resolved),
    ):
        return await AttachmentTextExtractor.extract(refs, draft, agent_class="A", agent_id="a")


@pytest.mark.asyncio
async def test_readable_text_is_returned_capped_to_the_character_limit():
    long_text = "x" * 500
    results = await _extract([_ref("invoice.pdf", 40_000)], _settings(attachment_char_limit=100), _loader(long_text))

    assert results[0].outcome is AttachmentOutcome.TEXT
    assert results[0].text == "x" * 100


@pytest.mark.asyncio
async def test_an_empty_extraction_is_reported_as_holding_no_text():
    """What MinerU answers for a photo. Not an error, and not something to feed the model as content."""
    results = await _extract([_ref("cat.jpg", 84_000, "image/jpeg")], _settings(), _loader(""))

    assert results[0].outcome is AttachmentOutcome.NO_TEXT
    assert results[0].text == ""
    assert "no text could be extracted" in results[0].inventory_line


@pytest.mark.asyncio
async def test_an_extraction_of_only_figure_references_counts_as_holding_no_text():
    """A bare image reference is the parser saying "there is a picture here", not the document's content."""
    results = await _extract([_ref("cat.jpg", 84_000, "image/jpeg")], _settings(), _loader("![](cat.jpg)\n\n"))

    assert results[0].outcome is AttachmentOutcome.NO_TEXT


@pytest.mark.asyncio
async def test_a_file_type_no_loader_handles_is_reported_unreadable_without_being_fetched():
    load = AsyncMock(return_value=b"bytes")
    results = await _extract([_ref("archive.zip", 40_000, "application/zip")], _settings(), None, load)

    assert results[0].outcome is AttachmentOutcome.UNREADABLE
    assert load.await_count == 0, "an unreadable type must not cost an S3 fetch"


@pytest.mark.asyncio
async def test_a_loader_that_raises_costs_only_that_attachment():
    """Losing a whole run of drafts to one malformed PDF would be a far worse trade than drafting without it."""
    exploding = SimpleNamespace(aload_data_from_bytes=AsyncMock(side_effect=RuntimeError("bad pdf")))
    results = await _extract([_ref("invoice.pdf", 40_000)], _settings(), exploding)

    assert results[0].outcome is AttachmentOutcome.UNREADABLE
    assert "could not be read" in results[0].inventory_line


@pytest.mark.asyncio
async def test_an_attachment_below_the_size_floor_is_never_fetched():
    """The signature-logo case: parsing a 3 KB inline PNG costs a round trip and yields nothing."""
    load = AsyncMock(return_value=b"bytes")
    results = await _extract([_ref("logo.png", 3_000, "image/png")], _settings(min_attachment_bytes=8192), load=load)

    assert results == []
    assert load.await_count == 0


@pytest.mark.asyncio
async def test_only_the_largest_attachments_are_read_when_over_the_cap():
    """Size is the only signal left about which file is the substantive one — the MIME disposition is long gone."""
    refs = [
        _ref("small.pdf", 10_000),
        _ref("large.pdf", 90_000, file_id=_OTHER_FILE_ID),
    ]
    results = await _extract(refs, _settings(max_attachments_per_message=1))

    assert [result.filename for result in results] == ["large.pdf"]


@pytest.mark.asyncio
async def test_the_loader_is_called_without_image_extraction():
    """Every loader raises when asked for images with no filesystem to write them to, and a reply prompt has no use
    for them anyway."""
    loader = _loader("Invoice total 42.00")
    await _extract([_ref("invoice.pdf", 40_000)], _settings(), loader)

    assert loader.aload_data_from_bytes.await_args.kwargs["include_images"] is False


@pytest.mark.asyncio
async def test_the_inventory_line_names_the_file_its_type_and_its_size():
    results = await _extract([_ref("invoice.pdf", 40_960)], _settings())

    assert results[0].inventory_line == "invoice.pdf (application/pdf, 40 KB)"
