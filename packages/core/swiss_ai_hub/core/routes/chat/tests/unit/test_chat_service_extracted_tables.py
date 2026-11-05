"""Clients that read only answer text still get a table a model extracted in a tool loop, the answer ends with a link
to download the whole table, and an earlier table comes back to the agent as one line."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from llama_index.core.base.llms.types import ChatMessage, ImageBlock, MessageRole, TextBlock

from swiss_ai_hub.core.events.agent.control.stop.stop_event import StopEvent
from swiss_ai_hub.core.events.agent.display.chunk_event import ChunkEvent
from swiss_ai_hub.core.events.agent.record_extraction.records_extracted_event import RecordsExtractedEvent
from swiss_ai_hub.core.generative_ai.structured_extraction.extracted_table_file import ExtractedTableFile
from swiss_ai_hub.core.generative_ai.structured_extraction.extracted_table_markup import ExtractedTableMarkup
from swiss_ai_hub.core.routes.chat.chat_service import ChatService, StreamingResources
from swiss_ai_hub.core.subscribers.agent.agent_nc_subscriber import AgentNCSubscriber
from swiss_ai_hub.core.topic_managers.agents.agent_topic_manager import AgentTopicManager
from swiss_ai_hub.core.topics.agents.agent_instance_topic import AgentInstanceTopic

TABLE = ExtractedTableMarkup.wrap("| Path | item |\n| --- | --- |\n| a.pdf | Rack |", rows=1)
TOPIC = AgentInstanceTopic(
    agent_class="UniversalAgent",
    agent_id="assistant",
    thread_id="t1",
    display_id="d1",
    run_id="r1",
    event_type=AgentTopicManager.DISPLAY_EVENT,
    event_name="RecordsExtractedEvent",
    event_id="e1",
)


def test_a_table_extracted_for_a_tool_call_becomes_answer_text_where_it_arrived():
    event = RecordsExtractedEvent(extraction_id="x", table=TABLE, summary="**Files:** 1", tool_call_id="c1")

    chunk = ChatService.extracted_table_chunk(event, TOPIC)

    assert isinstance(chunk, ChunkEvent)
    assert chunk.content == f"\n\n{TABLE}\n\n**Files:** 1\n\n"
    assert chunk.created_at == event.created_at
    assert chunk.model_name == "UniversalAgent/assistant"


def test_a_blueprints_own_table_and_a_tableless_result_add_nothing():
    chunk_of_blueprint = ChatService.extracted_table_chunk(
        RecordsExtractedEvent(extraction_id="x", table=TABLE, summary="s"), TOPIC
    )
    assert chunk_of_blueprint is None
    assert (
        ChatService.extracted_table_chunk(
            RecordsExtractedEvent(extraction_id="x", summary="s", tool_call_id="c"), TOPIC
        )
        is None
    )


def test_an_earlier_table_is_condensed_before_the_message_is_sent_on():
    messages = [
        ChatMessage(role=MessageRole.USER, content="all hardware lines"),
        ChatMessage(role=MessageRole.ASSISTANT, content=f"{TABLE}\n\n**Files:** 1"),
        ChatMessage(role=MessageRole.USER, content=f"what about {TABLE}?"),
    ]

    condensed = ChatService._without_earlier_tables(messages)

    assert condensed[1].content == "[A table of 1 extracted rows was shown here.]\n\n**Files:** 1"
    assert condensed[0] is messages[0]
    assert condensed[2] is messages[2]


def test_a_lost_answer_stream_is_still_completed_after_a_table_was_shown():
    table = ChatService.extracted_table_chunk(
        RecordsExtractedEvent(extraction_id="x", table=TABLE, summary="**Files:** 1", tool_call_id="c1"), TOPIC
    )
    streamed = [ChunkEvent(content="Here is "), table]
    stop = StopEvent(output_messages=[ChatMessage(role=MessageRole.ASSISTANT, content="Here is the table.")])

    content = ChatService.build_json_response_content(streamed, stop).content

    assert content.endswith("the table.")
    assert TABLE in content


def test_condensing_an_earlier_answer_keeps_its_other_blocks():
    image = ImageBlock(url="https://example.com/chart.png")
    answer = ChatMessage(role=MessageRole.ASSISTANT, blocks=[TextBlock(text=f"{TABLE}\n\nDone."), image])

    condensed = ChatService._without_earlier_tables([answer])[0]

    assert condensed.blocks[1] == image
    assert condensed.blocks[0].text == "[A table of 1 extracted rows was shown here.]\n\nDone."


def test_a_table_sent_back_with_windows_line_endings_is_condensed_too():
    crlf = TABLE.replace("\n", "\r\n")

    assert (
        ExtractedTableMarkup.condensed(f"{crlf}\r\nDone.") == "[A table of 1 extracted rows was shown here.]\r\nDone."
    )


FILE = ExtractedTableFile(
    bucket="agent-files", key="record-extraction/x/invoices.csv", filename="invoices.csv", size=9000, row_count=250
)
URL = "https://s3.example.com/agent-files/record-extraction/x/invoices.csv?X-Amz-Signature=abc"
DOWNLOAD = f"\n\nDownload the full table (250 rows): [invoices.csv]({URL})"


@pytest.fixture
def presigned():
    with patch(
        "swiss_ai_hub.core.routes.chat.chat_service.ExtractionFileStore.download_url", return_value=URL
    ) as download_url:
        yield download_url


def _stored(tool_call_id: str | None = None) -> RecordsExtractedEvent:
    return RecordsExtractedEvent(
        extraction_id="x",
        table=TABLE,
        file=FILE,
        summary="**Files:** 1",
        row_count=1,
        total_row_count=250,
        tool_call_id=tool_call_id,
    )


def test_a_stored_table_is_offered_for_download_with_its_row_count(presigned: MagicMock):
    assert ChatService.extracted_table_download(_stored(), "en") == DOWNLOAD
    presigned.assert_called_once_with(FILE)


def test_the_download_is_offered_in_the_answers_language_and_dropped_from_later_history_in_any(
    presigned: MagicMock,
):
    german = ChatService.extracted_table_download(_stored(), "de")

    assert german == f"\n\nGanze Tabelle herunterladen (250 Zeilen): [invoices.csv]({URL})"
    assert ChatService._is_table_download_text(german)
    assert ChatService._is_table_download_text(ChatService.extracted_table_download(_stored(), "fr"))


def test_a_table_from_before_tables_were_stored_and_other_events_offer_no_download(presigned: MagicMock):
    old = RecordsExtractedEvent(extraction_id="x", table=TABLE, summary="s", tool_call_id="c1")

    assert ChatService.extracted_table_download(old) == ""
    assert ChatService.extracted_table_download(ChunkEvent(content="Here")) == ""
    assert ChatService.extracted_table_chunk(old, TOPIC).content == f"\n\n{TABLE}\n\ns\n\n"
    presigned.assert_not_called()


def test_brackets_in_a_file_name_do_not_break_the_link(presigned: MagicMock):
    event = _stored().model_copy(update={"file": FILE.model_copy(update={"filename": "a [draft].csv"})})

    assert "[a \\[draft\\].csv](" in ChatService.extracted_table_download(event)


def _download_chunk() -> ChunkEvent:
    return ChatService.table_downloads_chunk([DOWNLOAD], TOPIC)


def test_the_download_ends_the_answer_after_the_part_that_was_not_streamed():
    streamed = [ChunkEvent(content="Here is "), _download_chunk()]
    stop = StopEvent(output_messages=[ChatMessage(role=MessageRole.ASSISTANT, content="Here is the table.")])

    content = ChatService.build_json_response_content(streamed, stop).content

    assert content == f"Here is the table.{DOWNLOAD}"


def test_a_download_does_not_keep_the_answer_from_extending_what_was_streamed():
    assert ChatService.answer_text(["Here is ", DOWNLOAD, "the"]) == "Here is the"


def test_no_download_chunk_without_a_stored_table():
    assert ChatService.table_downloads_chunk([], TOPIC) is None


@pytest.mark.asyncio
async def test_a_stream_holds_the_download_back_until_every_chunk_is_out():
    resources = StreamingResources(stop_signal=asyncio.Event(), subscriber=MagicMock(), chunk_queue=asyncio.Queue())
    for event in [ChunkEvent(content="Preview"), _download_chunk(), ChunkEvent(content=" and summary.")]:
        resources.chunk_queue.put_nowait(event)
    resources.stop_signal.set()

    streamed = [event.content async for event in ChatService.iter_streamed_display_events(resources, 0.01)]

    assert streamed == ["Preview", " and summary.", DOWNLOAD]


@pytest.mark.asyncio
async def test_an_agents_preview_streamed_after_the_event_still_comes_before_the_download(presigned: MagicMock):
    """The Knowledge Extraction Agent streams its preview and summary as chunks after the event naming the file."""
    with patch.object(AgentNCSubscriber, "for_thread_display_events") as for_thread:
        for_thread.return_value.start = AsyncMock()
        for_thread.return_value.stop = AsyncMock()
        resources = await ChatService.start_json_event_interaction(
            MagicMock(), "UniversalAgent", "assistant", MagicMock(), MagicMock(), MagicMock(), AsyncMock()
        )
        handler = for_thread.call_args.kwargs["handler"]
        await handler(_stored(), TOPIC)
        await handler(ChunkEvent(content=f"{TABLE}\n"), TOPIC)
        await handler(ChunkEvent(content="\n**Files:** 1"), TOPIC)
        answer = ChatMessage(role=MessageRole.ASSISTANT, content=f"{TABLE}\n\n**Files:** 1")
        await handler(StopEvent(output_messages=[answer]), TOPIC)

    content = ChatService.build_json_response_content(resources.chunk_events, resources.stop_event).content

    assert content == f"{TABLE}\n\n**Files:** 1{DOWNLOAD}"


def test_an_earlier_download_line_does_not_go_back_to_the_agent():
    answer = ChatMessage(role=MessageRole.ASSISTANT, content=f"{TABLE}\n\n**Files:** 1{DOWNLOAD}")

    condensed = ChatService._without_earlier_tables([answer])[0]

    assert condensed.content == "[A table of 1 extracted rows was shown here.]\n\n**Files:** 1"
