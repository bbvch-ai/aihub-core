"""
The record-extraction capability through the real dispatcher (NATS + Valkey), with the documents, object storage and
every model call stubbed.

What the step-level tests cannot show: the per-document fan-out and the join really run as separate dispatches, a
result delivered twice is counted once, two extractions started in one step stay apart, a selection too large to
extract unasked leaves its sample awaiting in the thread, a "yes" in a later run extracts every document in one
answer, and hundreds of documents finish in one answer within a bound.
Marked self_hosted: needs the dev stack's NATS and Valkey, nothing else.
"""

import asyncio
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any, ClassVar
from unittest.mock import MagicMock

import pytest
from bson import ObjectId
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.agents import AgentConfig
from swiss_ai_hub.core.events.agent import ExtractRecordsEvent, RecordsExtractedEvent, StopEvent, UserMessageEvent
from swiss_ai_hub.core.generative_ai import (
    BucketNamespacePair,
    DocumentExtractionResult,
    ExtractedTableFile,
    ExtractionFileStore,
    KnowledgeDocument,
    KnowledgeDocumentCriteria,
    KnowledgeDocumentSelection,
    KnowledgeDocumentSelectionResult,
    KnowledgeDocumentSummary,
    LLMConfig,
    RecordField,
    RecordProvenance,
    RecordSchema,
)
from swiss_ai_hub.core.i18n import LocaleString
from swiss_ai_hub.core.testing import async_test
from swiss_ai_hub.core.testing.auth_utils import fake_user
from swiss_ai_hub.core.topic_managers import AgentTopicManager

from swiss_ai_hub.agent.agents.agent import Agent
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_config import KnowledgeDocumentConfig
from swiss_ai_hub.agent.capabilities.record_extraction.document_extracted_event import DocumentExtractedEvent
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_sample import SAMPLE_DOCUMENTS
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_table import PREVIEW_ROWS
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction import RecordExtraction
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_config import RecordExtractionConfig
from swiss_ai_hub.agent.capabilities.record_extraction.record_extraction_fields import RecordExtractionFields
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString
from swiss_ai_hub.agent.runners.agent_test_runner import AgentTestRunner
from swiss_ai_hub.agent.workflow.decorators.precondition import precondition
from swiss_ai_hub.agent.workflow.decorators.step import step

pytestmark = pytest.mark.self_hosted

PLANNER = "swiss_ai_hub.agent.capabilities.record_extraction.extraction_planner"
EXTRACTION = "swiss_ai_hub.agent.capabilities.record_extraction.document_record_extraction"
FINANCE = BucketNamespacePair(bucket_name="finance-db", namespace_name="invoices")
SCHEMA = RecordSchema(
    fields=[
        RecordField(name="item", type="string", description="The billed item."),
        RecordField(name="amount", type="number", description="The amount in CHF."),
    ]
)
# One answer over 500 stubbed documents: every document is its own dispatch and the join re-checks every result. About
# 10 s on the development stack; the bound catches a join that grows quadratically or a dispatch that serialises.
FIVE_HUNDRED_DOCUMENTS_SECONDS = 60


def _selection(term: str) -> KnowledgeDocumentSelection:
    return KnowledgeDocumentSelection(any_of=[KnowledgeDocumentCriteria(content_query=term)])


@precondition()
async def every_table_arrived(event: UserMessageEvent, tables: list[RecordsExtractedEvent]) -> bool:
    wanted = 2 if event.messages[-1].content == "two" else 1
    return len({table.extraction_id for table in tables}) >= wanted


class TablesConfig(RecordExtractionFields, AgentConfig):
    pass


class TablesAgent(Agent):
    """Calls the extraction the way a blueprint does: "two" starts two at once, "yes" confirms a sample."""

    name: ClassVar[AgentLocaleString] = AgentLocaleString(en="Tables")
    description: ClassVar[AgentLocaleString] = AgentLocaleString(en="Extraction fixture")

    @step()
    async def start_step(self, event: UserMessageEvent) -> list[ExtractRecordsEvent]:
        text = event.messages[-1].content
        if text == "yes":
            return [RecordExtraction.confirm_sample([FINANCE])]
        terms = ["ACME AG", "Globex"] if text == "two" else [text]
        return [RecordExtraction.extract(_selection(term), "item, amount", [FINANCE]) for term in terms]

    @step(precondition=every_table_arrived)
    async def stop_step(self, event: UserMessageEvent, tables: list[RecordsExtractedEvent]) -> StopEvent:
        return StopEvent()


class _Store:
    """`ExtractionFileStore` in memory, shared by every dispatch of the test's process."""

    def __init__(self) -> None:
        self.stored: dict[str, list[dict[str, Any]]] = {}
        self.tables: dict[str, list[list[Any]]] = {}

    async def put_rows(self, extraction_id: str, request_id: str, rows: list[dict[str, Any]]) -> str:
        key = f"record-extraction/{extraction_id}/rows/{request_id}.json"
        self.stored[key] = rows
        return key

    async def rows(self, key: str) -> list[dict[str, Any]]:
        return self.stored[key]

    async def put_table(
        self, extraction_id: str, filename: str, columns: list[str], rows: list[list[Any]]
    ) -> ExtractedTableFile:
        self.tables[extraction_id] = rows
        return ExtractedTableFile(
            bucket="agent-files",
            key=f"record-extraction/{extraction_id}/{filename}",
            filename=filename,
            size=len(rows),
            row_count=len(rows),
        )


def _config(**settings: Any) -> TablesConfig:
    return TablesConfig(
        agent_id=f"tables-{ObjectId()}",
        name=LocaleString(en="Tables"),
        description=LocaleString(en="Extraction fixture"),
        llm=LLMConfig(model_name="text-generation/dummy"),
        knowledge_documents=KnowledgeDocumentConfig(enabled=True),
        record_extraction=RecordExtractionConfig(**settings),
    )


def _document(path: str) -> KnowledgeDocumentSummary:
    return KnowledgeDocumentSummary(
        id=path.replace("/", "-"),
        collection=FINANCE,
        path=path,
        filename=path.rsplit("/", 1)[-1],
        title=path,
        file_type="pdf",
        number_of_pages=1,
        updated_at=datetime(2025, 1, 1, tzinfo=UTC),
    )


def _documents(count: int) -> list[KnowledgeDocumentSummary]:
    return [_document(f"invoices/{2024 + index % 2}/q{index % 4 + 1}/inv{index:04d}.pdf") for index in range(count)]


def _stub(monkeypatch: pytest.MonkeyPatch, selections: dict[str, list[KnowledgeDocumentSummary]], gate=None) -> _Store:
    by_id = {document.id: document for documents in selections.values() for document in documents}
    store = _Store()

    async def resolve(collections, selection, limit, restricting_glob=None, timeout_seconds=20.0):
        documents = selections[selection.any_of[0].content_query]
        return KnowledgeDocumentSelectionResult(documents=documents[:limit], truncated=len(documents) > limit)

    async def build(description, llm, t):
        return SCHEMA

    async def load(collections, document_id, start=None, end=None):
        return KnowledgeDocument(summary=by_id[document_id], text="Rack 310", text_length=8, start=0, end=8)

    async def extract(schema, document, llm, llm_config, t, instructions=None, **_):
        if gate is not None and document.summary.path.endswith("b.pdf"):
            await gate.wait()
        provenance = RecordProvenance.from_summary(document.summary)
        return DocumentExtractionResult.succeeded(provenance, [{"item": document.summary.path, "amount": 1.0}], 1)

    @asynccontextmanager
    async def cost_reporting(self, displayer, user=None):
        yield MagicMock()

    monkeypatch.setattr(f"{PLANNER}.KnowledgeDocumentSelector.resolve", resolve)
    monkeypatch.setattr(f"{PLANNER}.RecordSchemaBuilder.build", build)
    monkeypatch.setattr(f"{EXTRACTION}.KnowledgeDocumentReader.load_document", load)
    monkeypatch.setattr(f"{EXTRACTION}.RecordExtractor.extract", extract)
    monkeypatch.setattr(LLMConfig, "cost_reporting_llm", cost_reporting)
    monkeypatch.setattr(LLMConfig, "get_model_info", lambda self: {"model_info": {}})
    monkeypatch.setattr(ExtractionFileStore, "put_rows", store.put_rows)
    monkeypatch.setattr(ExtractionFileStore, "rows", store.rows)
    monkeypatch.setattr(ExtractionFileStore, "put_table", store.put_table)
    return store


def _message(text: str) -> UserMessageEvent:
    return UserMessageEvent(messages=[ChatMessage(content=text, role=MessageRole.USER)], user=fake_user(), locale="en")


def _control(runner: AgentTestRunner, event_class: type) -> list:
    return [
        observed.event
        for observed in runner.observed_events
        if isinstance(observed.event, event_class) and observed.topic.event_type == AgentTopicManager.CONTROL_EVENT
    ]


async def _answer(config: TablesConfig, text: str, thread_id: str, delay: int = 30) -> AgentTestRunner:
    runner = AgentTestRunner(agent_type=TablesAgent, agent_config=config)
    async with runner.test_run(delay_before_stop=delay, thread_id=thread_id) as topic:
        await runner.send_event_from_topic(topic=topic, start_event=_message(text))
    return runner


@async_test
async def test_every_document_is_extracted_and_joined_into_one_table(monkeypatch):
    store = _stub(monkeypatch, {"ACME AG": [_document("invoices/a.pdf"), _document("invoices/b.pdf")]})
    runner = AgentTestRunner(agent_type=TablesAgent, agent_config=_config())

    async with runner.test_run(delay_before_stop=30) as topic:
        await runner.send_event_from_topic(topic=topic, start_event=_message("ACME AG"))

    assert not runner.has_exception_event
    tables = _control(runner, RecordsExtractedEvent)
    assert len(tables) == 1
    assert (tables[0].file_count, tables[0].row_count, tables[0].total_row_count) == (2, 2, 2)
    assert tables[0].file.filename == f"table-{tables[0].extraction_id}.csv"
    assert len(store.tables[tables[0].extraction_id]) == 2
    assert all(result.rows_key in store.stored for result in _control(runner, DocumentExtractedEvent))
    assert len(_control(runner, StopEvent)) == 1


@async_test
async def test_a_result_delivered_twice_is_joined_once(monkeypatch):
    gate = asyncio.Event()
    _stub(monkeypatch, {"ACME AG": [_document("invoices/a.pdf"), _document("invoices/b.pdf")]}, gate)
    runner = AgentTestRunner(agent_type=TablesAgent, agent_config=_config())

    async with runner.test_run(delay_before_stop=30) as topic:
        await runner.send_event_from_topic(topic=topic, start_event=_message("ACME AG"))
        first = await runner.wait_for_event(DocumentExtractedEvent, timeout=20)
        await runner.send_event(first, topic.thread_id, topic.display_id, topic.run_id)
        await asyncio.sleep(1)
        gate.set()

    tables = _control(runner, RecordsExtractedEvent)
    assert len(tables) == 1
    assert (tables[0].file_count, tables[0].total_row_count) == (2, 2)


@async_test
async def test_two_extractions_started_at_once_stay_apart(monkeypatch):
    _stub(
        monkeypatch,
        {
            "ACME AG": [_document("invoices/a.pdf"), _document("invoices/b.pdf")],
            "Globex": [_document("invoices/g.pdf")],
        },
    )
    runner = AgentTestRunner(agent_type=TablesAgent, agent_config=_config())

    async with runner.test_run(delay_before_stop=30) as topic:
        await runner.send_event_from_topic(topic=topic, start_event=_message("two"))

    tables = sorted(_control(runner, RecordsExtractedEvent), key=lambda table: table.file_count)
    assert [(table.file_count, table.total_row_count) for table in tables] == [(1, 1), (2, 2)]
    assert "invoices/g.pdf" in tables[0].table
    assert "invoices/a.pdf" not in tables[0].table


@async_test
async def test_a_large_selection_shows_a_sample_and_a_yes_in_the_next_run_extracts_all_of_it(monkeypatch):
    store = _stub(monkeypatch, {"ACME AG": _documents(150)})
    config = _config()
    thread_id = str(ObjectId())

    first = await _answer(config, "ACME AG", thread_id)
    second = await _answer(config, "yes", thread_id, delay=90)
    again = await _answer(config, "yes", thread_id)

    sample = _control(first, RecordsExtractedEvent)[0]
    assert (sample.file_count, sample.awaiting_confirmation) == (SAMPLE_DOCUMENTS, True)
    assert sample.summary.startswith(f"**Sample:** {SAMPLE_DOCUMENTS} of 150 matching documents")
    assert "**150 documents match.**" in sample.summary
    whole = _control(second, RecordsExtractedEvent)[0]
    assert not second.has_exception_event
    assert (whole.file_count, whole.total_row_count, whole.awaiting_confirmation) == (150, 150, False)
    assert whole.row_count == PREVIEW_ROWS
    assert len(store.tables[whole.extraction_id]) == 150
    assert len({result.request_event_id for result in _control(second, DocumentExtractedEvent)}) == 150
    nothing = _control(again, RecordsExtractedEvent)[0]
    assert nothing.summary.startswith("There is no sampled table extraction to go on with")


@async_test
async def test_five_hundred_documents_are_extracted_in_one_answer_within_a_bound(monkeypatch):
    store = _stub(monkeypatch, {"ACME AG": _documents(500)})
    config = _config(max_parallel_extractions=8)
    thread_id = str(ObjectId())
    await _answer(config, "ACME AG", thread_id)

    started = time.monotonic()
    runner = await _answer(config, "yes", thread_id, delay=FIVE_HUNDRED_DOCUMENTS_SECONDS)
    elapsed = time.monotonic() - started

    assert not runner.has_exception_event
    tables = _control(runner, RecordsExtractedEvent)
    assert len(tables) == 1
    assert (tables[0].file_count, tables[0].total_row_count, tables[0].failed_count) == (500, 500, 0)
    assert len(store.tables[tables[0].extraction_id]) == 500
    assert elapsed < FIVE_HUNDRED_DOCUMENTS_SECONDS
