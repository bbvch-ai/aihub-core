"""Clients that read only answer text still get a table a model extracted in a tool loop, and an earlier table comes
back to the agent as one line."""

from llama_index.core.base.llms.types import ChatMessage, ImageBlock, MessageRole, TextBlock

from swiss_ai_hub.core.events.agent.control.stop.stop_event import StopEvent
from swiss_ai_hub.core.events.agent.display.chunk_event import ChunkEvent
from swiss_ai_hub.core.events.agent.record_extraction.records_extracted_event import RecordsExtractedEvent
from swiss_ai_hub.core.generative_ai.structured_extraction.extracted_table_markup import ExtractedTableMarkup
from swiss_ai_hub.core.routes.chat.chat_service import ChatService
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
