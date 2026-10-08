"""Structured extraction against real models through the dev stack's LiteLLM gateway.

`STRUCTURED_EXTRACTION_TEST_MODEL` picks the model for the acceptance tests (default gemma-4-31B-it).
`STRUCTURED_EXTRACTION_CONSISTENCY_MODELS`, a comma-separated list, opts into the schema consistency report; run it with
`-s` to see the table. It measures rather than asserts, because which model is consistent enough is a team decision.
"""

import os
from collections import Counter
from datetime import UTC, datetime

import pytest
from llama_index.llms.openai_like import OpenAILike

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document import KnowledgeDocument
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.resources.costs.llm_cost_tracker import LLMCostTracker
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.generative_ai.structured_extraction.record_extractor import RecordExtractor
from swiss_ai_hub.core.generative_ai.structured_extraction.record_field import RecordField
from swiss_ai_hub.core.generative_ai.structured_extraction.record_schema import RecordSchema
from swiss_ai_hub.core.generative_ai.structured_extraction.record_schema_builder import RecordSchemaBuilder
from swiss_ai_hub.core.i18n.locale_handler import LocaleHandler

pytestmark = pytest.mark.integration

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
        _LINE_SCHEMA, _document(_long_contract(), title="Hardware contract"), llm, llm_config, LocaleHandler("en")
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
        schema, _document(header + _long_contract(), title="Hardware contract"), llm, llm_config, LocaleHandler("en")
    )

    assert not result.failed, result.failure_reason
    assert result.window_count > 1
    assert [record.values["position"] for record in result.records] == [1, 2, 3, 4, 5, 6]
    assert {record.values["contract_number"] for record in result.records} == {"HW-2025-117"}
    assert {record.values["supplier"] for record in result.records} == {"Helvetic IT Supplies AG"}


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
