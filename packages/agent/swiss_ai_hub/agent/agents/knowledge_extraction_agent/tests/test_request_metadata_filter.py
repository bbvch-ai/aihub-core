"""A request naming a document type or a recorded value narrows the documents by what ingestion classified (#2348):
the reading carries the types and conditions, the form shows them, and the extraction and its summary report what the
filter kept, left out and could not tell. A request naming neither reads exactly as before."""

from datetime import UTC, datetime

import pytest
from swiss_ai_hub.core.generative_ai import (
    BucketNamespacePair,
    DocumentAttribute,
    DocumentAttributeCondition,
    DocumentMetadataCounts,
    DocumentMetadataFilter,
    DocumentType,
    KnowledgeDocumentSummary,
)

from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_answer import ExtractionRequestAnswer
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_answers import ExtractionRequestAnswers
from swiss_ai_hub.agent.agents.knowledge_extraction_agent.extraction_request_parts import ExtractionRequestParts
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_planner import ExtractionPlanner
from swiss_ai_hub.agent.capabilities.record_extraction.extraction_table import ExtractionTable
from swiss_ai_hub.agent.capabilities.record_extraction.selection_facets import SelectionFacets
from swiss_ai_hub.agent.i18n.agent_locale_handler import AgentLocaleHandler

T = AgentLocaleHandler("en")
HOOLI = DocumentAttributeCondition(attribute=DocumentAttribute.PARTIES, contains=" Hooli ")


def _reading(
    types: list[DocumentType] | None = None, conditions: list[DocumentAttributeCondition] | None = None
) -> ExtractionRequestAnswer:
    return ExtractionRequestAnswer(
        is_table_request=True,
        confirms_sample=False,
        locations=[],
        fields="contract number, notice period",
        document_condition="contracts with Hooli" if types or conditions else None,
        document_types=types or [],
        attribute_conditions=conditions or [],
        instructions=None,
        calculation=None,
        document_kind=None,
        row_terms=None,
        document_terms=None,
    )


def _summary(path: str, document_type: str | None) -> KnowledgeDocumentSummary:
    return KnowledgeDocumentSummary(
        id=path,
        collection=BucketNamespacePair(bucket_name="kb", namespace_name="legal"),
        path=path,
        filename=path,
        title=path,
        file_type="pdf",
        updated_at=datetime(2025, 1, 1, tzinfo=UTC),
        document_type=document_type,
        document_types=[document_type] if document_type else [],
    )


def test_a_request_naming_no_type_or_value_selects_as_before() -> None:
    assert _reading().selection.metadata_filter is None


def test_the_selection_carries_the_named_types_and_readable_values() -> None:
    unreadable = DocumentAttributeCondition(attribute=DocumentAttribute.DATE, at_least="soon")

    selection = _reading([DocumentType.CONTRACT], [HOOLI, unreadable]).selection

    assert selection.metadata_filter == DocumentMetadataFilter(
        types=[DocumentType.CONTRACT],
        conditions=[DocumentAttributeCondition(attribute=DocumentAttribute.PARTIES, contains="Hooli")],
    )


def test_the_form_shows_the_filter_with_the_users_condition() -> None:
    reading = _reading([DocumentType.CONTRACT], [HOOLI])

    parts = ExtractionRequestParts.of(reading, T)

    assert parts.documents == 'contracts with Hooli; recorded as contract, parties contains "Hooli"'
    assert ExtractionRequestParts.named(reading)["documents"]


def test_dropping_the_document_condition_drops_the_types_and_values() -> None:
    reading = _reading([DocumentType.CONTRACT], [HOOLI])

    answers = ExtractionRequestAnswers.of("Document Condition: Every document", reading, T)

    assert answers.reading.metadata_filter is None
    assert answers.reading.document_condition is None


def test_the_reading_is_shown_the_types_in_scope_with_their_attributes() -> None:
    documents = [
        _summary("a.pdf", "contract"),
        _summary("b.pdf", "contract"),
        _summary("c.pdf", None),
        _summary("d.pdf", "memo"),
    ]

    lines = SelectionFacets.document_types(documents).splitlines()

    assert len(lines) == 1
    assert lines[0].startswith("- contract (2): document_date, document_reference_number, document_issuer")


def test_a_scope_without_a_known_type_lists_none() -> None:
    assert SelectionFacets.document_types([_summary("c.pdf", None), _summary("d.pdf", "memo")]) == ""


def test_the_summary_names_the_filter_and_what_it_left_out() -> None:
    counts = DocumentMetadataCounts(matched=3, excluded=2, unknown=1, excluded_examples=["x.pdf", "y.pdf"])
    metadata_filter = DocumentMetadataFilter(types=[DocumentType.CONTRACT], conditions=[HOOLI.readable()])

    lines = ExtractionTable.metadata_lines(counts, T)

    assert lines[0].startswith("**Type and attributes:** 3 documents match · 2 left out · 1 kept")
    assert "x.pdf" in lines[1] and "y.pdf" in lines[1]
    assert ExtractionPlanner.describe_metadata(metadata_filter) == (
        "type `contract` and `document_parties` contains `Hooli`"
    )


@pytest.mark.parametrize(
    ("condition", "described"),
    [
        (DocumentAttributeCondition(attribute=DocumentAttribute.TOTAL_AMOUNT, at_least="10000"), ">= 10000"),
        (DocumentAttributeCondition(attribute=DocumentAttribute.TOTAL_AMOUNT, at_least="CHF 10'000"), ">= 10000 CHF"),
        (
            DocumentAttributeCondition(attribute=DocumentAttribute.DATE, at_least="2025-01", at_most="2025-03"),
            ">= 2025-01-01 and <= 2025-03-31",
        ),
    ],
)
def test_a_range_reads_as_its_bounds(condition: DocumentAttributeCondition, described: str) -> None:
    readable = condition.readable()
    assert readable is not None

    assert ExtractionPlanner.describe_metadata(DocumentMetadataFilter(conditions=[readable])).endswith(described)
