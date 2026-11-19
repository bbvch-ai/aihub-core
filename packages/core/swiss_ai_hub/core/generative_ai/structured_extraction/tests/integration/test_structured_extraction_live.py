"""Structured extraction against real models through the dev stack's LiteLLM gateway.

`STRUCTURED_EXTRACTION_TEST_MODEL` picks the model for the acceptance tests (default gemma-4-31B-it).
`STRUCTURED_EXTRACTION_CONSISTENCY_MODELS`, a comma-separated list, opts into the schema consistency report; run it with
`-s` to see the table. It measures rather than asserts, because which model is consistent enough is a team decision.
"""

import asyncio
import os
from collections import Counter
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from llama_index.llms.openai_like import OpenAILike

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document import KnowledgeDocument
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.resources.costs.llm_cost_tracker import LLMCostTracker
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.generative_ai.structured_extraction.document_match import DocumentMatch
from swiss_ai_hub.core.generative_ai.structured_extraction.record_extractor import RecordExtractor
from swiss_ai_hub.core.generative_ai.structured_extraction.record_field import RecordField
from swiss_ai_hub.core.generative_ai.structured_extraction.record_schema import RecordSchema
from swiss_ai_hub.core.generative_ai.structured_extraction.record_schema_builder import RecordSchemaBuilder
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

pytestmark = [pytest.mark.integration, pytest.mark.external]

_MODEL = os.environ.get("STRUCTURED_EXTRACTION_TEST_MODEL", "text-generation/gemma-4-31B-it")
_CONSISTENCY_MODELS = [m for m in os.environ.get("STRUCTURED_EXTRACTION_CONSISTENCY_MODELS", "").split(",") if m]
_CONSISTENCY_RUNS = 5
_INVOICE_DESCRIPTION = "invoice number, date, supplier, line description, amount, currency"

_INVOICE = """# Invoice INV-2025-0412

Supplier: Helvetic IT Supplies AG, Bahnhofstrasse 10, 8001 Zürich
Date: 2025-03-14
Customer: Acme Engineering GmbH

| Pos | Description | Amount | Currency |
|-----|-------------|--------|----------|
| 1 | Laptop Lenovo ThinkPad T14 | 1450.00 | CHF |
| 2 | Docking station USB-C | 289.00 | CHF |
| 3 | Monitor Dell U2723QE 27" | 612.50 | CHF |
| 4 | Microsoft 365 Business licence, 12 months | 264.00 | CHF |
| 5 | Mechanical keyboard | 129.90 | CHF |
| 6 | Antivirus subscription renewal | 59.00 | CHF |
| 7 | External SSD 2 TB | 189.00 | CHF |

Total: 2993.40 CHF. Payable within 30 days.
"""

_LINE_SCHEMA = RecordSchema(
    fields=[
        RecordField(name="position", type="integer", description="Position number of the invoice line"),
        RecordField(name="description", type="string", description="What the line bills for"),
        RecordField(name="amount", type="number", description="Billed amount of the line in CHF"),
    ]
)


def _windows_at_once() -> asyncio.Semaphore:
    """As the agents call the extractor: windows side by side, bounded."""
    return asyncio.Semaphore(4)


def _document(text: str, title: str = "Invoice INV-2025-0412") -> KnowledgeDocument:
    summary = KnowledgeDocumentSummary(
        id="live-doc",
        collection=BucketNamespacePair(bucket_name="kb", namespace_name="finance"),
        path="invoices/2025/helvetic.pdf",
        filename="helvetic.pdf",
        title=title,
        file_type="pdf",
        updated_at=datetime(2025, 3, 14, tzinfo=UTC),
    )
    return KnowledgeDocument(summary=summary, text=text, text_length=len(text), start=0, end=len(text))


def _long_contract() -> str:
    """Thirty pages of terms with six billed lines spread through it, the last on the final page."""
    filler = (
        "The contractor shall perform the services with the care of a diligent professional, keep all information "
        "received confidential, and inform the client without delay of any circumstance that may endanger the "
        "timely completion of the work. Clause {n} applies in addition to the general terms and conditions."
    )
    lines = {
        1: "Position 1: Rack server Dell PowerEdge R760, 8900.00 CHF.",
        80: "Position 2: Network switch Cisco C9300, 4200.00 CHF.",
        160: "Position 3: UPS APC Smart-UPS 3000, 1850.00 CHF.",
        240: "Position 4: Firewall appliance FortiGate 100F, 3100.00 CHF.",
        320: "Position 5: Backup NAS Synology RS3621, 5400.00 CHF.",
        399: "Position 6: Rack cabinet 42U with cabling, 1290.00 CHF.",
    }
    return "\n\n".join(lines.get(n, filler.format(n=n)) for n in range(400))


def _contract_header(supplier: str) -> str:
    return f"# Contract HW-2025-117\n\nSupplier: {supplier}\nClient: Acme Engineering GmbH\n\n"


def _llm() -> tuple[LLMConfig, OpenAILike, LLMCostTracker]:
    llm_config = LLMConfig(model_name=_MODEL)
    llm, cost_tracker = llm_config.to_llama_index()
    return llm_config, llm, cost_tracker


@pytest.mark.asyncio
async def test_invoice_description_yields_a_schema_with_those_fields() -> None:
    _, llm, _ = _llm()

    schema = await RecordSchemaBuilder.build(_INVOICE_DESCRIPTION, llm, LocaleHandler("en"))

    names = " ".join(schema.field_names)
    assert len(schema.fields) == 6
    assert all(concept in names for concept in ("invoice", "date", "supplier", "description", "amount", "currency"))


@pytest.mark.asyncio
async def test_five_hardware_lines_yield_five_records_and_are_costed() -> None:
    llm_config, llm, cost_tracker = _llm()

    result = await RecordExtractor.extract(
        _LINE_SCHEMA,
        _document(_INVOICE),
        llm,
        llm_config,
        LocaleHandler("en"),
        instructions="Only hardware positions. Software licences and subscriptions are not hardware.",
    )

    assert not result.failed, result.failure_reason
    assert sorted(record.values["position"] for record in result.records) == [1, 2, 3, 5, 7]
    assert {record.provenance.filename for record in result.records} == {"helvetic.pdf"}
    assert cost_tracker.get_total_costs().prompt_token_count > 0


@pytest.mark.asyncio
async def test_document_without_matching_content_yields_zero_records() -> None:
    llm_config, llm, _ = _llm()
    minutes = "Team meeting minutes, 3 March 2025. Discussed the summer party and the new coffee machine rota."

    result = await RecordExtractor.extract(_LINE_SCHEMA, _document(minutes), llm, llm_config, LocaleHandler("en"))

    assert not result.failed, result.failure_reason
    assert result.records == []


@pytest.mark.slow
@pytest.mark.asyncio
async def test_long_document_is_extracted_completely_without_duplicates() -> None:
    llm_config, llm, _ = _llm()

    result = await RecordExtractor.extract(
        _LINE_SCHEMA,
        _document(_long_contract(), title="Hardware contract"),
        llm,
        llm_config,
        LocaleHandler("en"),
        limiter=_windows_at_once(),
    )

    assert not result.failed, result.failure_reason
    assert result.window_count > 1
    assert [record.values["position"] for record in result.records] == [1, 2, 3, 4, 5, 6]


@pytest.mark.slow
@pytest.mark.asyncio
async def test_values_stated_once_in_the_header_reach_records_on_later_pages() -> None:
    llm_config, llm, _ = _llm()
    header = "# Contract HW-2025-117\n\nSupplier: Helvetic IT Supplies AG\nClient: Acme Engineering GmbH\n\n"
    schema = RecordSchema(
        fields=[
            RecordField(name="contract_number", type="string", description="Number of the contract, e.g. HW-2024-1"),
            RecordField(name="supplier", type="string", description="Company that supplies the positions"),
            *_LINE_SCHEMA.fields,
        ]
    )

    result = await RecordExtractor.extract(
        schema,
        _document(header + _long_contract(), title="Hardware contract"),
        llm,
        llm_config,
        LocaleHandler("en"),
        limiter=_windows_at_once(),
    )

    assert not result.failed, result.failure_reason
    assert result.window_count > 1
    assert [record.values["position"] for record in result.records] == [1, 2, 3, 4, 5, 6]
    assert {record.values["contract_number"] for record in result.records} == {"HW-2025-117"}
    assert {record.values["supplier"] for record in result.records} == {"Helvetic IT Supplies AG"}


@pytest.mark.slow
@pytest.mark.flaky
@pytest.mark.asyncio
async def test_long_markdown_table_is_extracted_once_per_row_with_exact_amounts() -> None:
    """A table row is one line, so a window edge inside it would hand the model a truncated amount.

    Flaky because the 300 rows come back as about 9,000 output tokens: under CI's 300 s timeout only while the provider
    generates faster than about 30 tokens/s, and it measured 21 on 2026-10-12 (421 s).
    """
    llm_config, llm, _ = _llm()
    amounts = {n: float(f"{50 + n * 7}.50") for n in range(1, 301)}
    rows = "\n".join(f"| {n} | External SSD 2 TB | {amount:.2f} | CHF |" for n, amount in amounts.items())
    table = f"# Invoice INV-2025-0977\n\n| Pos | Description | Amount | Currency |\n|---|---|---|---|\n{rows}\n"

    result = await RecordExtractor.extract(
        _LINE_SCHEMA,
        _document(table, title="Invoice INV-2025-0977"),
        llm,
        llm_config,
        LocaleHandler("en"),
        limiter=_windows_at_once(),
    )

    assert not result.failed, result.failure_reason
    assert result.window_count > 1
    assert {record.values["position"]: record.values["amount"] for record in result.records} == amounts
    assert len(result.records) == len(amounts)


@pytest.mark.asyncio
async def test_an_invoice_from_another_supplier_is_skipped_with_its_reason() -> None:
    llm_config, llm, _ = _llm()

    result = await RecordExtractor.extract(
        _LINE_SCHEMA,
        _document(_INVOICE),
        llm,
        llm_config,
        LocaleHandler("en"),
        document_condition="only invoices from Hooli",
    )

    assert result.skipped, result.document_match
    assert result.records == []
    assert "Helvetic" in result.document_match.reason


@pytest.mark.asyncio
async def test_an_invoice_from_the_named_supplier_is_extracted() -> None:
    llm_config, llm, _ = _llm()

    result = await RecordExtractor.extract(
        _LINE_SCHEMA,
        _document(_INVOICE),
        llm,
        llm_config,
        LocaleHandler("en"),
        document_condition="only invoices from Helvetic IT Supplies",
    )

    assert not result.skipped, result.document_match
    assert sorted(record.values["position"] for record in result.records) == [1, 2, 3, 4, 5, 6, 7]


@pytest.mark.asyncio
async def test_a_qualifying_invoice_still_keeps_only_the_rows_the_instructions_ask_for() -> None:
    """The judged window must not read "as if there were no document condition" as "keep every row"."""
    llm_config, llm, _ = _llm()

    result = await RecordExtractor.extract(
        _LINE_SCHEMA,
        _document(_INVOICE),
        llm,
        llm_config,
        LocaleHandler("en"),
        instructions="Only hardware positions. Software licences and subscriptions are not hardware.",
        document_condition="only invoices from Helvetic IT Supplies",
    )

    assert result.document_match.verdict == "yes", result.document_match
    assert sorted(record.values["position"] for record in result.records) == [1, 2, 3, 5, 7]


@pytest.mark.asyncio
async def test_an_invoice_without_a_supplier_line_in_its_opening_is_unsure() -> None:
    """An absent fact is not a contradiction, so the document is read and its rows are checked by a person."""
    llm_config, llm, _ = _llm()
    invoice = _INVOICE.replace("Supplier: Helvetic IT Supplies AG, Bahnhofstrasse 10, 8001 Zürich\n", "")

    result = await RecordExtractor.extract(
        _LINE_SCHEMA,
        _document(invoice),
        llm,
        llm_config,
        LocaleHandler("en"),
        document_condition="only invoices from Hooli",
    )

    assert result.document_match.verdict == "unsure", result.document_match
    assert sorted(record.values["position"] for record in result.records) == [1, 2, 3, 4, 5, 6, 7]


@pytest.mark.asyncio
async def test_an_invoice_that_writes_no_currency_is_unsure_under_a_currency_condition() -> None:
    """A currency guessed from the supplier's country is not stated, so it never fails the document."""
    llm_config, llm, _ = _llm()
    invoice = (
        _INVOICE.replace(" | Currency |", " |")
        .replace("|----------|", "|")
        .replace(" | CHF |", " |")
        .replace(" CHF.", ".")
    )

    result = await RecordExtractor.extract(
        _LINE_SCHEMA,
        _document(invoice),
        llm,
        llm_config,
        LocaleHandler("en"),
        document_condition="only invoices in GBP",
    )

    assert "CHF" not in invoice
    assert result.document_match.verdict == "unsure", result.document_match


@pytest.mark.slow
@pytest.mark.asyncio
async def test_a_long_contract_failing_the_condition_is_read_in_one_call() -> None:
    llm_config, llm, _ = _llm()
    predict = type(llm).astructured_predict

    with patch.object(type(llm), "astructured_predict", autospec=True, side_effect=predict) as calls:
        result = await RecordExtractor.extract(
            _LINE_SCHEMA,
            _document(_contract_header("Initech AG") + _long_contract(), title="Hardware contract"),
            llm,
            llm_config,
            LocaleHandler("en"),
            limiter=_windows_at_once(),
            document_condition="only contracts with Hooli",
        )

    assert result.window_count > 1
    assert result.skipped, result.document_match
    assert calls.await_count == 1


@pytest.mark.slow
@pytest.mark.asyncio
async def test_a_long_contract_signed_on_its_last_page_is_unsure_not_skipped() -> None:
    llm_config, llm, _ = _llm()
    signature = "\n\nSigned for the client: Anna Muster, Zürich, 2025-03-20. Signed for the supplier: Beat Keller."
    text = _contract_header("Helvetic IT Supplies AG") + _long_contract() + signature

    result = await RecordExtractor.extract(
        _LINE_SCHEMA,
        _document(text, title="Hardware contract"),
        llm,
        llm_config,
        LocaleHandler("en"),
        limiter=_windows_at_once(),
        document_condition="only signed versions",
    )

    assert result.window_count > 1
    assert result.document_match.verdict == "unsure", result.document_match
    assert [record.values["position"] for record in result.records] == [1, 2, 3, 4, 5, 6]


def _invoice(header: str) -> str:
    """`_INVOICE`'s lines under another header."""
    return header + _INVOICE[_INVOICE.index("| Pos |") :]


async def _judged(text: str, condition: str, locale: str = "en", title: str = "Invoice") -> DocumentMatch | None:
    llm_config, llm, _ = _llm()
    result = await RecordExtractor.extract(
        _LINE_SCHEMA, _document(text, title=title), llm, llm_config, LocaleHandler(locale), document_condition=condition
    )
    return result.document_match


@pytest.mark.asyncio
async def test_a_supplier_named_without_a_label_that_differs_is_no() -> None:
    text = _invoice("Umbra Logistik AG\nMusterweg 3, 4051 Basel\n\n# Invoice 2025-311\n\nDate: 2025-03-14\n\n")

    match = await _judged(text, "only invoices from Hooli AG")

    assert match.verdict == "no", match


@pytest.mark.asyncio
async def test_a_name_that_merely_contains_the_requested_name_is_another_party() -> None:
    text = _invoice("# Invoice 2025-312\n\nSupplier: Rosenberg AG, Seestrasse 4, 8002 Zürich\nDate: 2025-03-14\n\n")

    match = await _judged(text, "only invoices from Berg AG")

    assert match.verdict == "no", match


_OCR_HEADER = "# Invoice 2025-313\n\nSupplier: Vantra AG, Industriestrasse 21, 6300 Zug\nDate: 2025-03-14\n\n"


@pytest.mark.asyncio
async def test_a_misread_supplier_name_with_the_right_name_elsewhere_is_not_skipped() -> None:
    """The header lost a letter to OCR; the payment details still name the supplier (demo dry run, "Hooi AG").

    "yes" and "unsure" both keep the document; the model may read the payee as a variant of the header name.
    """
    text = _invoice(_OCR_HEADER) + "\nPlease transfer the amount to Vantora AG, IBAN CH93 0076 2011 6238 5295 7.\n"

    match = await _judged(text, "only invoices from Vantora AG")

    assert match.verdict in ("yes", "unsure"), match


_OTHER_SUPPLIER_HEADER = (
    "# Invoice 2025-314\n\nSupplier: Kestrel Mietwagen GmbH, Bahnhofstrasse 4, 8001 Zürich\nDate: 2025-03-14\n\n"
)


@pytest.mark.asyncio
async def test_a_requested_name_only_inside_a_web_address_does_not_meet_the_condition() -> None:
    """The real-invoice e2e kept a rental invoice whose note links to the requested supplier's website."""
    text = _invoice(_OTHER_SUPPLIER_HEADER) + "\nNote: more information at www.vantora.ch\n"

    match = await _judged(text, "only invoices from Vantora AG")

    assert match.verdict == "no", match


@pytest.mark.asyncio
async def test_a_supplier_name_a_letter_off_and_nowhere_else_is_unsure() -> None:
    match = await _judged(_invoice(_OCR_HEADER), "only invoices from Vantora AG")

    assert match.verdict == "unsure", match


@pytest.mark.asyncio
async def test_a_plain_invoice_does_not_meet_a_credit_note_condition() -> None:
    match = await _judged(_INVOICE, "only credit notes", title="Invoice INV-2025-0412")

    assert match.verdict == "no", match


@pytest.mark.asyncio
async def test_a_date_outside_the_quarter_is_no() -> None:
    match = await _judged(_INVOICE, "only invoices dated in Q2 2025", title="Invoice INV-2025-0412")

    assert match.verdict == "no", match


@pytest.mark.asyncio
async def test_a_german_condition_on_a_german_invoice_from_another_supplier_is_no() -> None:
    text = _invoice(
        "# Rechnung RE-2025-118\n\nLieferant: Alpenblick Bürobedarf AG, Hauptgasse 9, 3011 Bern\nDatum: 14.03.2025\n\n"
    )

    match = await _judged(text, "nur Rechnungen von Hooli AG", locale="de", title="Rechnung RE-2025-118")

    assert match.verdict == "no", match


@pytest.mark.asyncio
async def test_a_french_condition_on_a_french_invoice_from_another_supplier_is_no() -> None:
    text = _invoice(
        "# Facture F-2025-77\n\nFournisseur : Papeterie du Lac SA, Rue du Rhône 12, 1204 Genève\nDate : 14.03.2025\n\n"
    )

    match = await _judged(text, "seulement les factures de Hooli SA", locale="fr", title="Facture F-2025-77")

    assert match.verdict == "no", match


@pytest.mark.asyncio
async def test_a_date_only_condition_keeps_a_credit_note_dated_inside_the_period() -> None:
    """A condition that names no document type never fails a document for its type (regression of e2e D06b)."""
    text = _invoice(
        "# Credit Note CN-2025-031\n\nSupplier: Helvetic IT Supplies AG, Bahnhofstrasse 10, 8001 Zürich\n"
        "Date: 2025-03-14\nRefers to invoice INV-2025-0412\n\n"
    )

    match = await _judged(text, "dated between 1 January 2025 and 31 March 2025", title="Credit Note CN-2025-031")

    assert match.verdict == "yes", match


@pytest.mark.asyncio
async def test_a_german_date_only_condition_keeps_a_gutschrift_dated_inside_the_period() -> None:
    text = _invoice(
        "# Gutschrift GS-2025-031\n\nLieferant: Alpenblick Bürobedarf AG, Hauptgasse 9, 3011 Bern\n"
        "Datum: 14.03.2025\nZu Rechnung RE-2025-118\n\n"
    )

    match = await _judged(
        text, "datiert zwischen dem 1. Januar 2025 und dem 31. März 2025", locale="de", title="Gutschrift GS-2025-031"
    )

    assert match.verdict == "yes", match


_DRAFT_SPEC = """# Payment Service Specification

Document status: DRAFT
Author: Platform Engineering department
Version: 0.3

## Requirements

REQ-1: The service shall confirm every payment within two seconds.
REQ-2: The service shall keep an audit log of every refund for ten years.
REQ-3: The service shall reject payments above CHF 50,000 without a second approval.
"""
_REQUIREMENT_SCHEMA = RecordSchema(
    fields=[
        RecordField(name="requirement_id", type="string", description="Identifier of the requirement, e.g. REQ-1"),
        RecordField(name="text", type="string", description="What the requirement demands"),
    ]
)


async def _judged_spec(condition: str) -> DocumentMatch | None:
    llm_config, llm, _ = _llm()
    result = await RecordExtractor.extract(
        _REQUIREMENT_SCHEMA,
        _document(_DRAFT_SPEC, title="Payment Service Specification"),
        llm,
        llm_config,
        LocaleHandler("en"),
        document_condition=condition,
    )
    return result.document_match


@pytest.mark.asyncio
async def test_a_draft_meets_a_condition_that_asks_for_no_status() -> None:
    """Drafts are routine for specifications and policies; only a condition on status may fail them (review M1)."""
    match = await _judged_spec("documents written by the Platform Engineering department")

    assert match.verdict == "yes", match


@pytest.mark.asyncio
async def test_a_draft_fails_a_condition_that_asks_for_approved_documents() -> None:
    match = await _judged_spec("only approved, final documents")

    assert match.verdict == "no", match


@pytest.mark.slow
@pytest.mark.asyncio
async def test_a_long_contract_naming_its_supplier_only_after_the_first_window_is_unsure() -> None:
    """The sharpened "no" must stay limited to a stated value: a supplier that window 0 does not show is unsure."""
    llm_config, llm, _ = _llm()
    header = "# Contract HW-2025-117\n\nClient: Acme Engineering GmbH\n\n"
    supplier = "\n\nThe supplier under this contract is Hooli AG, Bahnhofplatz 1, 8001 Zürich."

    result = await RecordExtractor.extract(
        _LINE_SCHEMA,
        _document(header + _long_contract() + supplier, title="Hardware contract"),
        llm,
        llm_config,
        LocaleHandler("en"),
        limiter=_windows_at_once(),
        document_condition="only contracts whose supplier is Hooli AG",
    )

    assert result.window_count > 1
    assert result.document_match.verdict == "unsure", result.document_match
    assert [record.values["position"] for record in result.records] == [1, 2, 3, 4, 5, 6]


@pytest.mark.skipif(not _CONSISTENCY_MODELS, reason="set STRUCTURED_EXTRACTION_CONSISTENCY_MODELS to measure")
@pytest.mark.asyncio
@pytest.mark.parametrize("model_name", _CONSISTENCY_MODELS)
async def test_schema_consistency_report(model_name: str) -> None:
    llm, _ = LLMConfig(model_name=model_name).to_llama_index()
    outcomes: Counter[str] = Counter()
    for _ in range(_CONSISTENCY_RUNS):
        try:
            schema = await RecordSchemaBuilder.build(_INVOICE_DESCRIPTION, llm, LocaleHandler("en"))
            outcomes[", ".join(f"{f.name}:{f.type}" for f in schema.fields)] += 1
        except ValueError as unusable:
            outcomes[f"FAILED {type(unusable).__name__}"] += 1

    print(f"\n{model_name}: {outcomes.most_common(1)[0][1]}/{_CONSISTENCY_RUNS} runs share the most common schema")
    for signature, count in outcomes.most_common():
        print(f"  {count}x {signature}")
    assert outcomes.total() == _CONSISTENCY_RUNS
