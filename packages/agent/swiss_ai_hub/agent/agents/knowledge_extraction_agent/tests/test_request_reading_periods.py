"""The request reading against a live model: a period that dates the documents is written as dates into period_start
and period_end, never as a year location (with year folders in scope, once the first reading drops the date folders
that only repeat the period), never into the document condition and, on invoice totals, never into instructions; a
request without a period gets none, and a period on rows that carry their own date goes into instructions alone. A form
answer that writes a period into Document Condition moves it out of the condition, and one that asks for every document
drops the period.

Needs LiteLLM with `text-generation/gemma-4-31B-it` and the provider behind it. Run with:

    cd packages/agent
    uv run pytest swiss_ai_hub/agent/agents/knowledge_extraction_agent/tests/test_request_reading_periods.py -m external
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from swiss_ai_hub.core.displayers import EventDisplayer
from swiss_ai_hub.core.generative_ai import BucketNamespacePair, LLMConfig

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_answer import ExtractionRequestAnswer
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_answers import ExtractionRequestAnswers
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_form import ExtractionRequestForm
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_parts import ExtractionRequestParts
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_reading import ExtractionRequestReading
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_collection import (
    KnowledgeDocumentCollection,
)
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_run_scope import (
    KnowledgeDocumentRunScope,
)
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_form import FORM, ExtractionForm
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler

pytestmark = pytest.mark.external

MODEL = "text-generation/gemma-4-31B-it"
FINANCE = BucketNamespacePair(bucket_name="finance-db", namespace_name="invoices")
SCOPE = KnowledgeDocumentRunScope(
    collections=[KnowledgeDocumentCollection(identifier="finance/invoices", collection=FINANCE, label="Finance")]
)
FOLDERS = "invoices/2025 (14), invoices/2024 (18), invoices/2025/q1 (8), statements (6)"
FACETS = [
    "**By folder:** invoices (40), statements (6)",
    "**By year in the path:** 2024 (18), 2025 (22), 2026 (6)",
]


YEAR_FOLDER_FACETS = [
    "**By folder:** invoices/2025 (6), invoices/2024 (3), invoices/2025/q1 (2), invoices (2)",
    "**By year in the path:** 2025 (6), 2024 (3)",
]


MIXED_KINDS = "The folders hold supplier invoices and credit notes side by side."


async def _read(
    locale: str, message: str, facets: list[str] = FACETS, notes: str | None = None
) -> ExtractionRequestAnswer:
    return await _read_history(locale, [ChatMessage(role=MessageRole.USER, content=message)], facets, notes)


async def _read_history(
    locale: str, history: list[ChatMessage], facets: list[str] = FACETS, notes: str | None = None
) -> ExtractionRequestAnswer:
    displayer = MagicMock(spec=EventDisplayer)
    displayer.display_llm_costs = AsyncMock()
    reading = await ExtractionRequestReading.ask(
        history,
        SCOPE,
        facets,
        notes,
        False,
        LLMConfig(model_name=MODEL),
        displayer,
        None,
        AgentLocaleHandler(locale),
    )
    assert reading is not None
    return reading


async def _second_reading(
    locale: str, message: str, reply: str
) -> tuple[ExtractionRequestAnswer, ExtractionRequestAnswers]:
    """The model's reading of a reply typed to the request form, before the confirm step applies the parts the reply
    dropped, and the answers that apply them."""
    t = AgentLocaleHandler(locale)
    understood = await _read(locale, message)
    places = [t(f"{FORM}.where.folders", folders=FOLDERS)]
    parts = ExtractionRequestParts.of(understood, t).form(understood, places, t)
    question = ExtractionForm.text(parts, [], t)
    answers = ExtractionRequestAnswers.of(reply, understood, t)
    assert answers.correction is not None
    history = ExtractionRequestForm.answered([ChatMessage(role=MessageRole.USER, content=message)], question, reply)
    return await _read_history(locale, history), answers


def _places(reading: ExtractionRequestAnswer) -> str:
    return " ".join(f"{location.path_glob} {location.path_regex}" for location in reading.locations)


@pytest.mark.asyncio
async def test_a_year_is_read_as_a_period_not_a_location():
    reading = await _read("en", "Hardware lines of the 2025 invoices")

    assert (reading.period_start, reading.period_end) == ("2025-01-01", "2025-12-31")
    assert "2025" not in _places(reading)
    assert "2025" not in (reading.document_condition or "")
    assert "2025" not in (reading.instructions or "")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("locale", "message", "period"),
    [
        ("en", "invoice totals 2025", ("2025-01-01", "2025-12-31")),
        ("en", "invoice totals Q1 2025", ("2025-01-01", "2025-03-31")),
        ("en", "Totals of all invoices dated 2025", ("2025-01-01", "2025-12-31")),
        ("de", "Rechnungsbeträge aus dem Jahr 2025", ("2025-01-01", "2025-12-31")),
        ("en", "amounts of the invoices from the first quarter of 2025", ("2025-01-01", "2025-03-31")),
    ],
)
async def test_a_period_a_year_folder_below_carries_is_no_location_after_the_first_reading(
    locale: str, message: str, period: tuple[str, str]
):
    """e2e N1: with year folders in the facets, Kimi read "invoice totals 2025" as invoices/2025/** plus the period,
    which left out every undated invoice. The prompt names this case and the first reading drops such date folders;
    the assertion covers both together, as the agent runs them. The paraphrases are not the prompt's example."""
    raw = await _read(locale, message, YEAR_FOLDER_FACETS)
    reading = raw.without_period_folders(message)

    assert (reading.period_start, reading.period_end) == period
    assert "2025" not in _places(reading)
    assert "q1" not in _places(reading).lower()


@pytest.mark.asyncio
@pytest.mark.xfail(
    strict=False,
    reason="Gemma restates the quarter in document_condition next to the period (e2e F3 class, accepted in the ADR)",
)
async def test_a_period_in_words_is_not_restated_in_the_document_condition():
    reading = await _read("en", "amounts of the invoices from the first quarter of 2025", YEAR_FOLDER_FACETS)

    assert "2025" not in (reading.document_condition or "")


@pytest.mark.asyncio
async def test_a_kind_that_leaves_out_other_documents_in_scope_is_a_document_condition():
    """Review S1: the kind the whole request is about is no condition, but credit notes among invoices are the #2347
    case of a condition the whole document meets or fails."""
    reading = await _read("en", "credit note totals 2025", notes=MIXED_KINDS)

    assert (reading.period_start, reading.period_end) == ("2025-01-01", "2025-12-31")
    assert "credit" in (reading.document_condition or "").lower()
    assert "2025" not in (reading.document_condition or "")


@pytest.mark.asyncio
async def test_a_quarter_is_read_as_its_first_and_last_day():
    reading = await _read("de", "Rechnungen aus Q1 2026")

    assert (reading.period_start, reading.period_end) == ("2026-01-01", "2026-03-31")


@pytest.mark.asyncio
async def test_a_period_without_an_end_has_no_end():
    reading = await _read("fr", "factures depuis mars 2025")

    assert (reading.period_start, reading.period_end) == ("2025-03-01", None)


@pytest.mark.asyncio
async def test_a_request_without_a_period_keeps_its_condition_and_gets_no_period():
    reading = await _read("it", "tutte le righe hardware delle fatture di Hooli")

    assert (reading.period_start, reading.period_end) == (None, None)
    assert "Hooli" in (reading.document_condition or "")


@pytest.mark.asyncio
async def test_a_request_without_a_period_or_a_condition_gets_neither():
    reading = await _read("en", "every line item with its amount")

    assert (reading.period_start, reading.period_end, reading.document_condition) == (None, None, None)


@pytest.mark.asyncio
async def test_a_date_the_rows_carry_stays_in_the_instructions():
    reading = await _read("en", "bookings in March 2025 on the yearly statement")

    assert (reading.period_start, reading.period_end) == (None, None)
    assert "2025" in (reading.instructions or "") or "march" in (reading.instructions or "").lower()


@pytest.mark.asyncio
async def test_a_period_on_statement_lines_filters_the_rows_and_dates_no_document():
    """e2e F4: with the period on the document alone, every line of a statement spanning it was kept; a period on the
    document would leave out a statement whose path names its later issue date (round-3 review S2)."""
    reading = await _read("en", "statement lines from February 2025")
    instructions = (reading.instructions or "").lower()

    assert (reading.period_start, reading.period_end) == (None, None)
    assert "2025" in instructions
    assert "feb" in instructions or "2025-02" in instructions


@pytest.mark.asyncio
@pytest.mark.parametrize(("locale", "message"), [("en", "invoice totals Q1 2025"), ("de", "Rechnungssummen Q1 2025")])
async def test_a_period_on_invoice_totals_dates_the_documents_not_the_rows(locale: str, message: str):
    """An invoice total carries the invoice's date, yet the period dates the invoice: in instructions it would filter
    rows and add the match column to every period request on invoices (round-3 review S3)."""
    reading = await _read(locale, message)
    instructions = (reading.instructions or "").lower()

    assert (reading.period_start, reading.period_end) == ("2025-01-01", "2025-03-31")
    assert "2025" not in instructions
    assert "q1" not in instructions
    assert "quart" not in instructions


@pytest.mark.asyncio
async def test_a_period_written_into_document_condition_leaves_the_condition():
    """e2e F3: "dated 2024" was kept as the condition next to the period."""
    second, answers = await _second_reading("en", "invoice totals 2025", "Document Condition: dated 2024")
    reading = answers.applied(second)

    assert (reading.period_start, reading.period_end) == ("2024-01-01", "2024-12-31")
    assert "2024" not in (reading.document_condition or "")


@pytest.mark.asyncio
async def test_every_document_written_into_document_condition_drops_the_period():
    """e2e F2: the second reading kept the period read from the first message. The code drops it again for this exact
    line whatever the model reads, so the confirmed outcome is what is checked (review suggestion 7)."""
    second, answers = await _second_reading(
        "en", "invoice totals 2025", "Document Condition: every document at the location"
    )
    reading = answers.applied(second)

    assert (reading.period_start, reading.period_end, reading.document_condition) == (None, None, None)
