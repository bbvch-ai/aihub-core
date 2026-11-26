import asyncio
import re
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, call

import pytest
from llama_index.core.prompts.rich import RichPromptTemplate
from pydantic import BaseModel

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document import KnowledgeDocument
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.generative_ai.structured_extraction import record_extractor
from swiss_ai_hub.core.generative_ai.structured_extraction.record_extractor import RecordExtractor
from swiss_ai_hub.core.generative_ai.structured_extraction.record_field import RecordField
from swiss_ai_hub.core.generative_ai.structured_extraction.record_schema import RecordSchema
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

pytestmark = pytest.mark.unit

_LINE = re.compile(r"Position (\d+): (\w+) item costs (\d+) CHF\.")

_FIXTURES = Path(__file__).parent / "fixtures"

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
        collection_name="kb/finance",
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


def _rows(text: str) -> list[dict[str, Any]]:
    return [{"position": int(n), "amount": float(a)} for n, _, a in _LINE.findall(text)]


def _reading_llm() -> Mock:
    """A model that extracts exactly the lines present in the window it is shown, as a faithful model would."""

    def answer(records_model: type[BaseModel], _prompt: Any, **window_args: Any) -> BaseModel:
        return records_model(records=_rows(window_args["text"]))

    llm = Mock()
    llm.astructured_predict = AsyncMock(side_effect=answer)
    return llm


def _judging_llm(verdict: str, reason: str = "Supplier: Initech AG", records_in_no: bool = False) -> Mock:
    """As `_reading_llm`, and on the judged window it states `verdict` before the records it read."""

    def answer(records_model: type[BaseModel], _prompt: Any, **window_args: Any) -> BaseModel:
        rows = _rows(window_args["text"])
        if "document_match" not in records_model.model_fields:
            return records_model(records=rows)
        kept = rows if verdict != "no" or records_in_no else []
        return records_model(document_match={"verdict": verdict, "reason": reason}, records=kept)

    llm = Mock()
    llm.astructured_predict = AsyncMock(side_effect=answer)
    return llm


def _is_judged(awaited_call: Any) -> bool:
    return "document_match" in awaited_call.args[0].model_fields


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
    assert window_args["field_names"] == "position, amount, record_match"
    assert window_args["instructions"] == "only hardware"
    assert (window_args["position"], window_args["total"]) == (1, 1)


@pytest.mark.asyncio
async def test_windows_running_side_by_side_yield_the_records_of_one_by_one() -> None:
    document = _document(_invoice(400))
    config = _llm_config(max_output_tokens=600)

    sequential = await RecordExtractor.extract(_SCHEMA, document, _reading_llm(), config, LocaleHandler("en"))
    parallel = await RecordExtractor.extract(
        _SCHEMA, document, _reading_llm(), config, LocaleHandler("en"), limiter=asyncio.Semaphore(4)
    )

    assert sequential.window_count > 1
    assert [record.values for record in parallel.records] == [record.values for record in sequential.records]


@pytest.mark.asyncio
async def test_the_limiter_bounds_the_model_calls_running_at_once() -> None:
    running, most = 0, 0
    reading = _reading_llm()
    answer = reading.astructured_predict.side_effect

    async def slow(records_model: type[BaseModel], prompt: Any, **window_args: Any) -> BaseModel:
        nonlocal running, most
        running += 1
        most = max(most, running)
        await asyncio.sleep(0.01)
        running -= 1
        return answer(records_model, prompt, **window_args)

    reading.astructured_predict = AsyncMock(side_effect=slow)

    await RecordExtractor.extract(
        _SCHEMA,
        _document(_invoice(400)),
        reading,
        _llm_config(max_output_tokens=600),
        LocaleHandler("en"),
        limiter=asyncio.Semaphore(2),
    )

    assert most == 2


@pytest.mark.asyncio
async def test_a_long_document_is_read_in_part_and_says_so() -> None:
    text = _invoice(400) + "\n\nPosition 999: special item costs 5 CHF."

    result = await RecordExtractor.extract(
        _SCHEMA,
        _document(text),
        _reading_llm(),
        _llm_config(max_output_tokens=600),
        LocaleHandler("en"),
        max_windows=2,
        row_terms="special",
    )

    assert result.partial
    assert result.window_count > 2
    positions = [record.values["position"] for record in result.records]
    assert 1 in positions
    assert 999 in positions


@pytest.mark.asyncio
async def test_a_record_carrying_only_its_match_mark_is_dropped() -> None:
    llm = Mock()

    def answer(records_model: type[BaseModel], _prompt: Any, **_window_args: Any) -> BaseModel:
        empty = {"position": None, "amount": None, "record_match": "yes"}
        kept = {"position": 1, "amount": 5.0, "record_match": "unsure"}
        return records_model(records=[empty, kept])

    llm.astructured_predict = AsyncMock(side_effect=answer)

    result = await RecordExtractor.extract(
        _SCHEMA, _document(_invoice(1)), llm, _llm_config(), LocaleHandler("en"), instructions="only hardware"
    )

    assert [record.values for record in result.records] == [{"position": 1, "amount": 5.0, "record_match": "unsure"}]


def _rendered_prompt(locale: str, instructions: str, document_condition: str) -> str:
    """Every message of the extraction prompt, as the fixtures captured from main hold it."""
    t = LocaleHandler(locale)
    schema = _SCHEMA.with_match() if instructions else _SCHEMA
    messages = RichPromptTemplate(t("lib.prompt.structured_extraction.extraction_prompt")).format_messages(
        fields=schema.fields,
        field_names=", ".join(schema.field_names),
        instructions=instructions,
        document_condition=document_condition,
        title="Acme invoice",
        text="Position 7: hardware item costs 700 CHF.",
        position=2,
        total=3,
        opening="Invoice INV-7 from Acme AG.",
    )
    return "\n".join(f"[{message.role.value}]\n{message.content}" for message in messages) + "\n"


@pytest.mark.parametrize("locale", ["en", "de", "fr", "it"])
@pytest.mark.parametrize(("variant", "instructions"), [("plain", ""), ("instructions", "only hardware")])
def test_the_prompt_without_a_condition_equals_main(locale: str, variant: str, instructions: str) -> None:
    expected = (_FIXTURES / f"extraction_prompt_{locale}_{variant}.txt").read_text()

    assert _rendered_prompt(locale, instructions, document_condition="") == expected


@pytest.mark.parametrize(("instructions", "number"), [("", 8), ("only hardware", 9)])
def test_the_prompt_with_a_condition_adds_the_block_and_the_rule(instructions: str, number: int) -> None:
    rendered = _rendered_prompt("en", instructions, document_condition="only contracts with Hooli")

    assert "<document_condition>\nonly contracts with Hooli\n</document_condition>" in rendered
    assert f"\n{number}. The document condition decides whether the whole document counts." in rendered


@pytest.mark.asyncio
async def test_a_document_that_clearly_fails_the_condition_yields_no_records() -> None:
    result = await RecordExtractor.extract(
        _SCHEMA,
        _document(_invoice(5)),
        _judging_llm("no"),
        _llm_config(),
        LocaleHandler("en"),
        document_condition="only invoices from Hooli",
    )

    assert result.skipped
    assert not result.failed
    assert result.records == []
    assert result.document_match.reason == "Supplier: Initech AG"


@pytest.mark.asyncio
async def test_records_returned_with_a_no_verdict_are_dropped() -> None:
    result = await RecordExtractor.extract(
        _SCHEMA,
        _document(_invoice(5)),
        _judging_llm("no", records_in_no=True),
        _llm_config(),
        LocaleHandler("en"),
        document_condition="only invoices from Hooli",
    )

    assert result.skipped
    assert result.records == []


@pytest.mark.asyncio
async def test_a_long_document_failing_the_condition_is_read_only_in_its_first_window() -> None:
    llm = _judging_llm("no")

    result = await RecordExtractor.extract(
        _SCHEMA,
        _document(_invoice(300)),
        llm,
        _llm_config(max_output_tokens=600),
        LocaleHandler("en"),
        limiter=asyncio.Semaphore(4),
        document_condition="only invoices from Hooli",
    )

    assert result.window_count > 1
    assert result.skipped
    assert llm.astructured_predict.await_count == 1


@pytest.mark.asyncio
async def test_a_qualifying_long_document_reads_its_other_windows_after_the_first() -> None:
    llm = _judging_llm("yes", reason="Supplier: Hooli AG")

    result = await RecordExtractor.extract(
        _SCHEMA,
        _document(_invoice(300)),
        llm,
        _llm_config(max_output_tokens=600),
        LocaleHandler("en"),
        limiter=asyncio.Semaphore(4),
        document_condition="only invoices from Hooli",
    )

    first, *others = llm.astructured_predict.await_args_list
    assert _is_judged(first)
    assert first.kwargs["document_condition"] == "only invoices from Hooli"
    assert others
    assert not any(_is_judged(other) for other in others)
    assert all(other.kwargs["document_condition"] == "" for other in others)
    assert [record.values["position"] for record in result.records] == list(range(1, 301))
    assert result.document_match.verdict == "yes"


@pytest.mark.asyncio
async def test_with_a_condition_the_first_window_runs_alone() -> None:
    running, alongside_first = 0, []
    judging = _judging_llm("yes")
    answer = judging.astructured_predict.side_effect

    async def slow(records_model: type[BaseModel], prompt: Any, **window_args: Any) -> BaseModel:
        nonlocal running
        running += 1
        await asyncio.sleep(0.01)
        if window_args["position"] == 1:
            alongside_first.append(running)
        running -= 1
        return answer(records_model, prompt, **window_args)

    judging.astructured_predict = AsyncMock(side_effect=slow)

    await RecordExtractor.extract(
        _SCHEMA,
        _document(_invoice(400)),
        judging,
        _llm_config(max_output_tokens=600),
        LocaleHandler("en"),
        limiter=asyncio.Semaphore(4),
        document_condition="only invoices from Hooli",
    )

    assert alongside_first == [1]
    assert judging.astructured_predict.await_count > 2


@pytest.mark.asyncio
async def test_a_yes_verdict_extracts_the_same_records_as_without_a_condition() -> None:
    document, config = _document(_invoice(5)), _llm_config()
    t = LocaleHandler("en")

    plain = await RecordExtractor.extract(_SCHEMA, document, _judging_llm("yes"), config, t)
    judged = await RecordExtractor.extract(
        _SCHEMA, document, _judging_llm("yes"), config, t, document_condition="only invoices from Hooli"
    )

    assert [record.values for record in judged.records] == [record.values for record in plain.records]
    assert plain.document_match is None
    assert judged.document_match.verdict == "yes"


@pytest.mark.asyncio
async def test_an_unsure_document_is_read_whole_as_today() -> None:
    document, config = _document(_invoice(300)), _llm_config(max_output_tokens=600)
    t = LocaleHandler("en")
    llm = _judging_llm("unsure", reason="The excerpt names no supplier.")

    plain = await RecordExtractor.extract(_SCHEMA, document, _reading_llm(), config, t)
    unsure = await RecordExtractor.extract(_SCHEMA, document, llm, config, t, document_condition="only Hooli")

    assert not unsure.skipped
    assert unsure.document_match.unsure
    assert llm.astructured_predict.await_count == unsure.window_count
    assert [record.values for record in unsure.records] == [record.values for record in plain.records]


@pytest.mark.asyncio
async def test_a_malformed_first_window_fails_the_document_and_reads_no_other() -> None:
    llm = Mock()
    llm.astructured_predict = AsyncMock(side_effect=ValueError("no usable content"))

    result = await RecordExtractor.extract(
        _SCHEMA,
        _document(_invoice(300)),
        llm,
        _llm_config(max_output_tokens=600),
        LocaleHandler("en"),
        document_condition="only Hooli",
    )

    assert result.failed
    assert not result.skipped
    assert result.failure_reason.startswith("Excerpt 1 of")
    assert llm.astructured_predict.await_count == 1


@pytest.mark.asyncio
async def test_without_a_condition_no_window_is_judged_and_all_run_side_by_side() -> None:
    running, most = 0, 0
    reading = _reading_llm()
    answer = reading.astructured_predict.side_effect

    async def slow(records_model: type[BaseModel], prompt: Any, **window_args: Any) -> BaseModel:
        nonlocal running, most
        running += 1
        most = max(most, running)
        await asyncio.sleep(0.01)
        running -= 1
        return answer(records_model, prompt, **window_args)

    reading.astructured_predict = AsyncMock(side_effect=slow)

    result = await RecordExtractor.extract(
        _SCHEMA,
        _document(_invoice(400)),
        reading,
        _llm_config(max_output_tokens=600),
        LocaleHandler("en"),
        limiter=asyncio.Semaphore(2),
    )

    assert most == 2
    assert not any(_is_judged(awaited) for awaited in reading.astructured_predict.await_args_list)
    assert result.document_match is None


@pytest.mark.asyncio
async def test_an_empty_document_with_a_condition_makes_no_call() -> None:
    llm = _judging_llm("no")

    result = await RecordExtractor.extract(
        _SCHEMA, _document(""), llm, _llm_config(), LocaleHandler("en"), document_condition="only Hooli"
    )

    assert not result.skipped
    assert result.records == []
    llm.astructured_predict.assert_not_awaited()


@pytest.mark.asyncio
async def test_a_partly_read_document_failing_the_condition_reads_one_window() -> None:
    llm = _judging_llm("no")

    result = await RecordExtractor.extract(
        _SCHEMA,
        _document(_invoice(400)),
        llm,
        _llm_config(max_output_tokens=600),
        LocaleHandler("en"),
        max_windows=3,
        document_condition="only Hooli",
    )

    assert result.skipped
    assert llm.astructured_predict.await_count == 1


@pytest.mark.asyncio
async def test_the_verdict_and_reason_are_set_on_the_current_span(monkeypatch: pytest.MonkeyPatch) -> None:
    span = MagicMock()
    monkeypatch.setattr(record_extractor, "trace", SimpleNamespace(get_current_span=lambda: span))
    document, config, t = _document(_invoice(5)), _llm_config(), LocaleHandler("en")

    await RecordExtractor.extract(_SCHEMA, document, _judging_llm("no"), config, t)
    assert span.set_attribute.call_count == 0

    await RecordExtractor.extract(_SCHEMA, document, _judging_llm("no"), config, t, document_condition="only Hooli")
    assert span.set_attribute.call_args_list == [
        call("extraction.document.path", "invoices/2025/acme.pdf"),
        call("extraction.document_condition.verdict", "no"),
        call("extraction.document_condition.reason", "Supplier: Initech AG"),
    ]
