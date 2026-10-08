import re
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from pydantic import BaseModel

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document import KnowledgeDocument
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.generative_ai.structured_extraction.record_extractor import RecordExtractor
from swiss_ai_hub.core.generative_ai.structured_extraction.record_field import RecordField
from swiss_ai_hub.core.generative_ai.structured_extraction.record_schema import RecordSchema
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

pytestmark = pytest.mark.unit

_LINE = re.compile(r"Position (\d+): (\w+) item costs (\d+) CHF\.")

_SCHEMA = RecordSchema(
    fields=[
        RecordField(name="position", type="integer", description="Line number"),
        RecordField(name="amount", type="number", description="Line amount in CHF"),
    ]
)


def _document(text: str, start: int = 0, end: int | None = None) -> KnowledgeDocument:
    summary = KnowledgeDocumentSummary(
        id="doc-1",
        collection=BucketNamespacePair(bucket_name="kb", namespace_name="finance"),
        path="invoices/2025/acme.pdf",
        filename="acme.pdf",
        title="Acme invoice",
        file_type="pdf",
        updated_at=datetime(2025, 1, 1, tzinfo=UTC),
    )
    end = len(text) if end is None else end
    return KnowledgeDocument(summary=summary, text=text[start:end], text_length=len(text), start=start, end=end)


def _invoice(lines: int, kind: str = "hardware") -> str:
    return "\n\n".join(f"Position {n}: {kind} item costs {n * 100} CHF." for n in range(1, lines + 1))


def _llm_config(max_input_tokens: int = 100_000, max_output_tokens: int = 8192) -> SimpleNamespace:
    """Counts whitespace-separated words as tokens, so window sizes in the tests are easy to reason about."""
    model_info = {"model_info": {"max_input_tokens": max_input_tokens, "max_output_tokens": max_output_tokens}}
    return SimpleNamespace(model_name="test-model", token_counter=str.split, get_model_info=lambda: model_info)


def _reading_llm() -> Mock:
    """A model that extracts exactly the lines present in the window it is shown, as a faithful model would."""

    def answer(records_model: type[BaseModel], _prompt: Any, **window_args: Any) -> BaseModel:
        rows = [{"position": int(n), "amount": float(a)} for n, _, a in _LINE.findall(window_args["text"])]
        return records_model(records=rows)

    llm = Mock()
    llm.astructured_predict = AsyncMock(side_effect=answer)
    return llm


@pytest.mark.asyncio
async def test_extracts_every_line_of_a_short_document_in_one_call() -> None:
    llm = _reading_llm()

    result = await RecordExtractor.extract(_SCHEMA, _document(_invoice(5)), llm, _llm_config(), LocaleHandler("en"))

    assert not result.failed
    assert result.window_count == 1
    assert [record.values for record in result.records] == [{"position": n, "amount": n * 100.0} for n in range(1, 6)]


@pytest.mark.asyncio
async def test_every_record_names_the_document_it_came_from() -> None:
    result = await RecordExtractor.extract(
        _SCHEMA, _document(_invoice(2)), _reading_llm(), _llm_config(), LocaleHandler("en")
    )

    provenance = {(r.provenance.document_id, r.provenance.path, r.provenance.filename) for r in result.records}
    assert provenance == {("doc-1", "invoices/2025/acme.pdf", "acme.pdf")}


@pytest.mark.asyncio
async def test_long_document_is_extracted_completely_without_boundary_duplicates() -> None:
    llm = _reading_llm()

    result = await RecordExtractor.extract(
        _SCHEMA, _document(_invoice(300)), llm, _llm_config(max_output_tokens=600), LocaleHandler("en")
    )

    assert result.window_count > 1
    assert llm.astructured_predict.await_count == result.window_count
    assert [record.values["position"] for record in result.records] == list(range(1, 301))


@pytest.mark.asyncio
async def test_later_windows_are_shown_the_document_opening_for_values_stated_once_in_the_header() -> None:
    llm = _reading_llm()
    text = "Invoice INV-7 from Acme AG.\n\n" + _invoice(300)

    await RecordExtractor.extract(
        _SCHEMA, _document(text), llm, _llm_config(max_output_tokens=600), LocaleHandler("en")
    )

    openings = [call.kwargs["opening"] for call in llm.astructured_predict.await_args_list]
    assert len(openings) > 1
    assert openings[0] == ""
    assert all(opening.startswith("Invoice INV-7 from Acme AG.") for opening in openings[1:])


@pytest.mark.asyncio
async def test_opening_ends_inside_the_first_window_so_it_cannot_yield_a_record_twice() -> None:
    llm = _reading_llm()

    await RecordExtractor.extract(
        _SCHEMA, _document(_invoice(300)), llm, _llm_config(max_output_tokens=600), LocaleHandler("en")
    )

    first_window, second_window = (call.kwargs for call in llm.astructured_predict.await_args_list[:2])
    opening_lines = set(_LINE.findall(second_window["opening"]))
    assert opening_lines
    assert opening_lines <= set(_LINE.findall(first_window["text"]))
    assert not opening_lines & set(_LINE.findall(second_window["text"]))


@pytest.mark.asyncio
async def test_a_document_that_fits_one_window_gets_no_opening() -> None:
    llm = _reading_llm()

    await RecordExtractor.extract(_SCHEMA, _document(_invoice(5)), llm, _llm_config(), LocaleHandler("en"))

    assert llm.astructured_predict.await_args.kwargs["opening"] == ""


@pytest.mark.asyncio
async def test_document_without_matching_content_yields_zero_records_not_a_failure() -> None:
    llm = Mock()
    llm.astructured_predict = AsyncMock(side_effect=lambda model, _prompt, **_kwargs: model(records=[]))

    result = await RecordExtractor.extract(
        _SCHEMA, _document("Meeting notes, nothing billed."), llm, _llm_config(), LocaleHandler("en")
    )

    assert not result.failed
    assert result.records == []


@pytest.mark.asyncio
async def test_all_null_records_are_dropped() -> None:
    llm = Mock()
    llm.astructured_predict = AsyncMock(
        side_effect=lambda model, _prompt, **_kwargs: model(
            records=[{"position": None, "amount": None}, {"position": 1, "amount": None}]
        )
    )

    result = await RecordExtractor.extract(_SCHEMA, _document("Position 1"), llm, _llm_config(), LocaleHandler("en"))

    assert [record.values for record in result.records] == [{"position": 1, "amount": None}]


@pytest.mark.asyncio
async def test_empty_document_makes_no_model_call() -> None:
    llm = _reading_llm()

    result = await RecordExtractor.extract(_SCHEMA, _document(""), llm, _llm_config(), LocaleHandler("en"))

    assert result.records == []
    assert result.window_count == 0
    assert not result.failed
    llm.astructured_predict.assert_not_awaited()


@pytest.mark.asyncio
async def test_malformed_output_fails_the_document_with_a_reason_instead_of_raising() -> None:
    llm = Mock()
    llm.astructured_predict = AsyncMock(side_effect=ValueError("no usable content"))

    result = await RecordExtractor.extract(_SCHEMA, _document(_invoice(3)), llm, _llm_config(), LocaleHandler("en"))

    assert result.failed
    assert result.records == []
    assert "Excerpt 1 of 1" in result.failure_reason
    assert "no usable content" in result.failure_reason
    assert result.provenance.path == "invoices/2025/acme.pdf"


@pytest.mark.asyncio
async def test_one_failed_window_fails_the_whole_document_rather_than_returning_a_partial_list() -> None:
    reading = _reading_llm()
    calls = {"count": 0}

    async def second_window_breaks(*args: Any, **kwargs: Any) -> BaseModel:
        calls["count"] += 1
        if calls["count"] == 2:
            raise ValueError("unterminated JSON")
        return await reading.astructured_predict(*args, **kwargs)

    llm = Mock()
    llm.astructured_predict = second_window_breaks

    result = await RecordExtractor.extract(
        _SCHEMA, _document(_invoice(300)), llm, _llm_config(max_output_tokens=600), LocaleHandler("en")
    )

    assert result.failed
    assert result.records == []
    assert result.failure_reason.startswith("Excerpt 2 of")


@pytest.mark.asyncio
async def test_infrastructure_errors_propagate() -> None:
    llm = Mock()
    llm.astructured_predict = AsyncMock(side_effect=ConnectionError("gateway down"))
    document, llm_config, t = _document(_invoice(3)), _llm_config(), LocaleHandler("en")

    with pytest.raises(ConnectionError):
        await RecordExtractor.extract(_SCHEMA, document, llm, llm_config, t)


@pytest.mark.asyncio
async def test_a_character_range_is_rejected_because_records_outside_it_would_be_lost() -> None:
    document, llm, llm_config, t = _document(_invoice(3), end=20), _reading_llm(), _llm_config(), LocaleHandler("en")

    with pytest.raises(ValueError, match="needs the whole document"):
        await RecordExtractor.extract(_SCHEMA, document, llm, llm_config, t)


@pytest.mark.asyncio
async def test_a_model_too_small_to_extract_with_raises_a_configuration_error() -> None:
    document, llm, t = _document(_invoice(3)), _reading_llm(), LocaleHandler("en")
    llm_config = _llm_config(max_output_tokens=200)

    with pytest.raises(ValueError, match="tokens per document window"):
        await RecordExtractor.extract(_SCHEMA, document, llm, llm_config, t)


@pytest.mark.asyncio
async def test_prompt_names_every_field_and_carries_the_instructions() -> None:
    llm = _reading_llm()

    await RecordExtractor.extract(
        _SCHEMA, _document(_invoice(1)), llm, _llm_config(), LocaleHandler("en"), instructions="only hardware"
    )

    window_args = llm.astructured_predict.await_args.kwargs
    assert window_args["field_names"] == "position, amount"
    assert window_args["instructions"] == "only hardware"
    assert (window_args["position"], window_args["total"]) == (1, 1)
