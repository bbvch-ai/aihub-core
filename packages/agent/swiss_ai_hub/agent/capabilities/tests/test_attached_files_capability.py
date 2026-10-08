"""The attached-files capability's contract: `read` always answers, and every attached document the user asked
about ends up either in the block or reported as unreadable.

Files arrive on every turn for the whole message branch, so a turn without attachments answers with an empty block
and a waiting step never hangs. Images are left out, since they already reach the model as image content.
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.events.agent import (
    AttachedFileEvent,
    AttachedFilesReadEvent,
    AttachedFileStatus,
    UserUploadedFile,
)
from swiss_ai_hub.core.generative_ai import CitationId, ExtractedDocument, LLMConfig
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler
from swiss_ai_hub.core.topics import AgentInstanceTopic

from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent import LLMWrappingAgent
from swiss_ai_hub.agent.agents.llm_wrapping_agent.llm_wrapping_agent_config import LLMWrappingAgentConfig
from swiss_ai_hub.agent.capabilities.attached_files.attached_file_reader import MAX_CONCURRENT_READS
from swiss_ai_hub.agent.capabilities.attached_files.attached_file_sections import AttachedFileSections
from swiss_ai_hub.agent.capabilities.attached_files.attached_files import AttachedFiles
from swiss_ai_hub.agent.capabilities.attached_files.attached_files_budget import AttachedFilesBudget
from swiss_ai_hub.agent.capabilities.attached_files.attached_files_config import AttachedFilesConfig
from swiss_ai_hub.agent.capabilities.conversation.conversation_fields import ConversationFields

READER_MODULE = "swiss_ai_hub.agent.capabilities.attached_files.attached_file_reader"
HISTORY = [ChatMessage(role=MessageRole.USER, content="Summarise section 4.")]


def _config() -> LLMWrappingAgentConfig:
    return LLMWrappingAgentConfig(
        agent_id="files-test",
        name=LocaleString(en="Files"),
        description=LocaleString(en="Files fixture"),
        system_prompt=LocaleString(en="You are helpful."),
        llm=LLMConfig(model_name="text-generation/dummy"),
    )


def _file(name: str, file_type: str = "application/pdf", file_id: str = "7f1c6a8e-3b2d-4c5e-9f10-2a3b4c5d6e7f"):
    return UserUploadedFile(filename=name, file_type=file_type, file_id=file_id)


def _document(content: str, pages: int | None = 3) -> ExtractedDocument:
    return ExtractedDocument(
        title="Handbook",
        content=content,
        content_type="application/pdf",
        source_filename="handbook.pdf",
        document_parser="MineruLoader",
        number_of_pages=pages,
    )


async def _read(
    files: list[UserUploadedFile],
    budget: int = 100_000,
    query: str = "",
    reserve_tokens: int = 0,
    cite_sources: bool = True,
    first_page: int | None = None,
    last_page: int | None = None,
) -> list:
    config = _config()
    with patch.object(ConversationFields, "input_budget", return_value=budget):
        return await AttachedFiles.read_step(
            LLMWrappingAgent(),
            request=AttachedFiles.read(files, HISTORY, query, reserve_tokens, cite_sources, first_page, last_page),
            topic=AgentInstanceTopic(
                agent_class="LLMWrappingAgent",
                agent_id="files-test",
                thread_id="t1",
                display_id="d1",
                run_id="r1",
                event_type="control_event",
                event_name="X",
                event_id="e1",
            ),
            conversation=config,
            files_config=config,
            t=LocaleHandler("en"),
        )


@pytest.mark.asyncio
async def test_no_attachment_answers_an_empty_block():
    events = await _read([])

    assert [type(event) for event in events] == [AttachedFilesReadEvent]
    assert events[0].block == []


@pytest.mark.asyncio
async def test_images_are_not_read_as_documents():
    with patch(f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=AsyncMock()) as extract:
        events = await _read([_file("photo.png", file_type="image/png")])

    extract.assert_not_awaited()
    assert events[-1].block == []


@pytest.mark.asyncio
async def test_the_full_text_reaches_the_block_with_a_source_event():
    text = "Section 4: vacation is 25 days."
    with patch(f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=AsyncMock(return_value=_document(text))):
        events = await _read([_file("handbook.pdf")])

    source, read = events
    assert isinstance(source, AttachedFileEvent)
    assert source.status == AttachedFileStatus.READ
    assert source.number_of_pages == 3
    assert text in (read.block[0].content or "")
    assert read.block[0].role == MessageRole.SYSTEM


@pytest.mark.asyncio
async def test_the_file_is_citable_by_the_id_its_event_carries():
    text = "Section 4: vacation is 25 days."
    with patch(f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=AsyncMock(return_value=_document(text))):
        source, read = await _read([_file("handbook.pdf")])

    content = read.block[0].content or ""
    assert source.citation_id == CitationId.of(source.file_id)
    assert f"<REFERENCE_DOCUMENT id='{source.citation_id}' source='handbook.pdf'" in content
    assert "[sbcd9ab]" in (read.block[1].content or "")
    assert source.content == text


@pytest.mark.asyncio
async def test_a_caller_without_a_source_list_is_not_asked_for_citations():
    with patch(f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=AsyncMock(return_value=_document("text"))):
        _, read = await _read([_file("handbook.pdf")], cite_sources=False)

    assert "[sbcd9ab]" not in (read.block[0].content or "")


@pytest.mark.asyncio
async def test_the_file_is_read_from_the_agents_own_upload_location():
    extract = AsyncMock(return_value=_document("text"))
    with patch(f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=extract):
        await _read([_file("handbook.pdf")])

    bucket, key = extract.await_args.args
    assert bucket == UserUploadedFile.AGENT_FILES_BUCKET
    assert key == "LLMWrappingAgent/files-test/7f1c6a8e-3b2d-4c5e-9f10-2a3b4c5d6e7f/handbook.pdf"


@pytest.mark.asyncio
async def test_an_unreadable_file_is_reported_not_dropped():
    with patch(
        f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=AsyncMock(side_effect=ValueError("corrupt PDF"))
    ):
        events = await _read([_file("broken.pdf")])

    source, read = events
    assert source.status == AttachedFileStatus.FAILED
    assert source.error == "corrupt PDF"
    assert "broken.pdf" in (read.block[0].content or "")
    assert "corrupt PDF" in (read.block[0].content or "")


@pytest.mark.asyncio
async def test_many_attachments_are_read_a_few_at_a_time_in_order():
    """A dozen PDFs read at once overran MinerU's three slots and ran out of their 503 retries together."""
    in_flight, peak = 0, 0

    async def extract(bucket: str, key: str, content_type: str) -> ExtractedDocument:
        nonlocal in_flight, peak
        in_flight += 1
        peak = max(peak, in_flight)
        await asyncio.sleep(0.01)
        in_flight -= 1
        return _document(f"Contents of {key.rsplit('/', 1)[-1]}")

    files = [
        _file(f"{year}_d.pdf", file_id=f"7f1c6a8e-3b2d-4c5e-9f10-2a3b4c5d6e{year % 100:02d}")
        for year in range(2014, 2026)
    ]
    with patch(f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=extract):
        events = await _read(files)

    assert peak == MAX_CONCURRENT_READS
    assert [event.filename for event in events[:-1]] == [file.filename for file in files]
    assert all(event.status == AttachedFileStatus.READ for event in events[:-1])


LONG_TEXT = " ".join(f"Sentence number {index} of the handbook." for index in range(4000))


@pytest.mark.asyncio
async def test_a_file_too_large_without_a_query_keeps_its_beginning():
    with patch(f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=AsyncMock(return_value=_document(LONG_TEXT))):
        events = await _read([_file("handbook.pdf")], budget=2_000)

    source, read = events
    content = read.block[0].content or ""
    assert source.status == AttachedFileStatus.TRUNCATED
    assert "Sentence number 0 " in content
    assert "Sentence number 3999" not in content
    assert "beginning" in (read.block[-1].content or "")


@pytest.mark.asyncio
async def test_a_file_too_large_keeps_the_sections_relevant_to_the_query():
    async def pick_last(self, sections: list, query: str) -> list:
        return list(reversed(sections))

    with (
        patch(f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=AsyncMock(return_value=_document(LONG_TEXT))),
        patch.object(AttachedFileSections, "rank", new=pick_last),
    ):
        events = await _read([_file("handbook.pdf")], budget=2_000, query="What does the last sentence say?")

    source, read = events
    content = read.block[0].content or ""
    assert source.status == AttachedFileStatus.TRUNCATED
    assert "Sentence number 3999" in content
    assert "Sentence number 0 " not in content
    assert "excerpts" in (read.block[-1].content or "")


@pytest.mark.asyncio
async def test_a_failing_ranking_falls_back_to_the_beginning():
    with (
        patch(f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=AsyncMock(return_value=_document(LONG_TEXT))),
        patch.object(AttachedFileSections, "rank", new=AsyncMock(side_effect=RuntimeError("reranker down"))),
    ):
        events = await _read([_file("handbook.pdf")], budget=2_000, query="Anything?")

    assert "Sentence number 0 " in (events[-1].block[0].content or "")


@pytest.mark.asyncio
async def test_reserved_room_is_left_free():
    text = " ".join(["word."] * 3000)
    with patch(f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=AsyncMock(return_value=_document(text))):
        whole = await _read([_file("a.pdf")], budget=100_000)
        reserved = await _read([_file("a.pdf")], budget=100_000, reserve_tokens=99_000)

    assert whole[0].status == AttachedFileStatus.READ
    assert reserved[0].status == AttachedFileStatus.TRUNCATED


@pytest.mark.asyncio
async def test_a_quote_in_the_filename_cannot_break_the_tag():
    with patch(f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=AsyncMock(return_value=_document("text"))):
        events = await _read([_file('say "hi".pdf')])

    assert "source='say &quot;hi&quot;.pdf'" in (events[-1].block[0].content or "")


class TestAttachedFilesBudget:
    @staticmethod
    def _counter(text: str) -> list[int]:
        return [0] * len(text.split())

    def test_small_files_fit_whole_next_to_a_large_one(self):
        rooms = AttachedFilesBudget(1_000, 1.0, self._counter).allocate(
            {"small": "one two three", "large": " ".join(["word."] * 5000)}
        )

        assert rooms["small"] is None
        assert rooms["large"] is not None
        assert rooms["large"] > 0

    def test_everything_fits_when_there_is_room(self):
        rooms = AttachedFilesBudget(10_000, 1.0, self._counter).allocate({"a": "alpha beta", "b": "gamma"})

        assert rooms == {"a": None, "b": None}

    def test_no_room_left(self):
        assert AttachedFilesBudget(0, 1.0, self._counter).allocate({"a": "alpha beta"}) == {"a": 0}


class TestAttachedFileSections:
    @staticmethod
    def _counter(text: str) -> list[int]:
        return [0] * len(text.split())

    def test_a_file_is_split_along_its_headings_like_ingested_knowledge(self):
        document = _document("# Handbook\n\nIntro.\n\n## Vacation\n\n25 days.\n\n## Remote\n\nThree days.")

        sections = AttachedFileSections.parse(document, "file-1", "handbook.pdf")

        assert [(section.h1, section.h2) for section in sections] == [
            ("Handbook", None),
            ("Handbook", "Vacation"),
            ("Handbook", "Remote"),
        ]
        assert {section.source for section in sections} == {"handbook.pdf"}
        assert {section.document_id for section in sections} == {"file-1"}

    def test_fills_the_room_in_rank_order_and_keeps_document_order(self):
        document = _document("# A\n\n" + "alpha " * 50 + "\n\n# B\n\n" + "beta " * 50 + "\n\n# C\n\n" + "gamma " * 50)
        alpha, beta, gamma = AttachedFileSections.parse(document, "file-1", "doc.pdf")
        picker = AttachedFileSections(AttachedFilesConfig(), self._counter, None)

        chosen = picker.fill([gamma, alpha, beta], room=110)

        assert chosen == [alpha, gamma]

    def test_cosine(self):
        assert AttachedFileSections.cosine([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
        assert AttachedFileSections.cosine([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


PAGE_BREAK = "<!-- PageBreak -->"


def _paged_document(pages: int, words_per_page: int = 5) -> ExtractedDocument:
    texts = [" ".join([f"page{page}text"] * words_per_page) for page in range(1, pages + 1)]
    return _document(f"\n{PAGE_BREAK}\n".join(texts), pages=pages)


@pytest.mark.asyncio
async def test_pages_asked_for_are_read_instead_of_searched():
    document = _paged_document(5)
    with patch(f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=AsyncMock(return_value=document)):
        source, read = await _read([_file("handbook.pdf")], query="what is on page 3", first_page=3, last_page=4)

    content = read.block[0].content or ""
    assert "page3text" in content and "page4text" in content
    assert "page2text" not in content and "page5text" not in content
    assert 'These are pages 3 to 4 of "handbook.pdf", which has 5 pages.' in (read.block[-1].content or "")
    assert source.status == AttachedFileStatus.TRUNCATED


@pytest.mark.asyncio
async def test_a_single_page_needs_no_last_page():
    document = _paged_document(3)
    with patch(f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=AsyncMock(return_value=document)):
        _, read = await _read([_file("handbook.pdf")], first_page=2)

    content = read.block[0].content or ""
    assert "page2text" in content and "page1text" not in content and "page3text" not in content


@pytest.mark.asyncio
async def test_pages_that_do_not_fit_are_cut_in_order_and_the_model_is_told_where():
    document = _paged_document(10, words_per_page=200)
    with patch(f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=AsyncMock(return_value=document)):
        _, read = await _read([_file("handbook.pdf")], budget=1_000, first_page=2, last_page=9)

    content = read.block[0].content or ""
    note = read.block[-1].content or ""
    assert "page2text" in content and "page9text" not in content
    assert "of the requested pages 2 to 9" in note and "continue from page" in note


@pytest.mark.asyncio
async def test_a_page_past_the_end_is_reported():
    document = _paged_document(3)
    with patch(f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=AsyncMock(return_value=document)):
        _, read = await _read([_file("handbook.pdf")], first_page=7)

    assert '"handbook.pdf" has only 3 pages, so there is no page 7.' in (read.block[-1].content or "")


@pytest.mark.asyncio
async def test_a_file_without_page_marks_is_read_whole_and_the_model_is_told():
    document = _document("Office text without pages.", pages=4)
    with patch(f"{READER_MODULE}.DocumentExtractor.extract_from_s3", new=AsyncMock(return_value=document)):
        _, read = await _read([_file("handbook.docx")], first_page=2)

    assert "Office text without pages." in (read.block[0].content or "")
    assert 'The pages of "handbook.docx" are not known' in (read.block[-1].content or "")
