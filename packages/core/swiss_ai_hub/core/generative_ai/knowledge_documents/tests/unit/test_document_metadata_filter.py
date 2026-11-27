from datetime import UTC, date, datetime

import pytest

from swiss_ai_hub.core.generative_ai.document.classification.document_attribute import DocumentAttribute
from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType
from swiss_ai_hub.core.generative_ai.knowledge_documents.document_attribute_condition import (
    DocumentAttributeCondition,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.document_metadata_counts import DocumentMetadataCounts
from swiss_ai_hub.core.generative_ai.knowledge_documents.document_metadata_filter import DocumentMetadataFilter
from swiss_ai_hub.core.generative_ai.knowledge_documents.document_metadata_verdict import DocumentMetadataVerdict
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_date_range import PathDateRange
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair

pytestmark = pytest.mark.unit

MATCH, EXCLUDED, UNKNOWN = (
    DocumentMetadataVerdict.MATCH,
    DocumentMetadataVerdict.EXCLUDED,
    DocumentMetadataVerdict.UNKNOWN,
)


def _document(
    document_type: str | None,
    secondary: list[str] | None = None,
    path: str = "a.pdf",
    **attributes: str | float | list[str] | None,
) -> KnowledgeDocumentSummary:
    return KnowledgeDocumentSummary(
        id=path,
        collection=BucketNamespacePair(bucket_name="kb", namespace_name="finance"),
        path=path,
        filename=path,
        title=path,
        file_type="pdf",
        updated_at=datetime(2025, 1, 1, tzinfo=UTC),
        document_type=document_type,
        document_types=[document_type, *(secondary or [])] if document_type else [],
        document_attributes={f"document_{key}": value for key, value in attributes.items()},
    )


def _condition(attribute: DocumentAttribute, **values: str) -> DocumentAttributeCondition:
    readable = DocumentAttributeCondition(attribute=attribute, **values).readable()
    assert readable is not None
    return readable


def test_an_unclassified_document_is_unknown_and_kept() -> None:
    assert DocumentMetadataFilter(types=[DocumentType.CONTRACT]).verdict(_document(None)) is UNKNOWN


def test_a_type_matches_the_primary_or_a_secondary_type() -> None:
    contracts = DocumentMetadataFilter(types=[DocumentType.CONTRACT])

    assert contracts.verdict(_document("contract")) is MATCH
    assert contracts.verdict(_document("letter", secondary=["contract"])) is MATCH
    assert contracts.verdict(_document("invoice")) is EXCLUDED


@pytest.mark.parametrize("document_type", ["other", "memo"])
def test_other_and_a_type_the_catalog_no_longer_holds_are_unknown(document_type: str) -> None:
    hooli_contracts = DocumentMetadataFilter(
        types=[DocumentType.CONTRACT], conditions=[_condition(DocumentAttribute.PARTIES, contains="Hooli")]
    )

    assert hooli_contracts.verdict(_document(document_type)) is UNKNOWN


def test_an_attribute_only_a_secondary_type_carries_is_unknown() -> None:
    large_invoices = DocumentMetadataFilter(
        types=[DocumentType.INVOICE], conditions=[_condition(DocumentAttribute.TOTAL_AMOUNT, at_least="10000")]
    )

    assert large_invoices.verdict(_document("email_thread", secondary=["invoice"])) is UNKNOWN
    assert large_invoices.verdict(_document("report", secondary=["policy"])) is EXCLUDED


def test_text_matches_when_the_value_contains_it_case_ignored() -> None:
    hooli = DocumentMetadataFilter(conditions=[_condition(DocumentAttribute.PARTIES, contains="hooli")])

    assert hooli.verdict(_document("contract", parties=["Pied Piper Inc.", "Hooli AG"])) is MATCH
    assert hooli.verdict(_document("contract", parties=["Pied Piper Inc."])) is EXCLUDED
    assert hooli.verdict(_document("contract", parties=[])) is UNKNOWN
    assert hooli.verdict(_document("contract", parties=None)) is UNKNOWN


def test_an_attribute_the_type_does_not_carry_excludes_the_document() -> None:
    issued = DocumentMetadataFilter(conditions=[_condition(DocumentAttribute.TOTAL_AMOUNT, at_least="1000")])

    assert issued.verdict(_document("report")) is EXCLUDED
    assert issued.verdict(_document("invoice", total_amount=None)) is UNKNOWN


def test_amounts_match_a_range() -> None:
    large = DocumentMetadataFilter(conditions=[_condition(DocumentAttribute.TOTAL_AMOUNT, at_least="1'000")])

    assert large.verdict(_document("invoice", total_amount=4860.35)) is MATCH
    assert large.verdict(_document("invoice", total_amount=999.0)) is EXCLUDED


def test_an_amount_in_another_or_no_recorded_currency_is_unknown() -> None:
    condition = _condition(DocumentAttribute.TOTAL_AMOUNT, at_least="CHF 10'000")
    large = DocumentMetadataFilter(conditions=[condition])

    assert condition.currency == "CHF"
    assert large.verdict(_document("invoice", total_amount=12_000.0, currency="CHF")) is MATCH
    assert large.verdict(_document("invoice", total_amount=9_000.0, currency="CHF")) is EXCLUDED
    assert large.verdict(_document("invoice", total_amount=9_800.0, currency="EUR")) is UNKNOWN
    assert large.verdict(_document("invoice", total_amount=500_000.0, currency="JPY")) is UNKNOWN
    assert large.verdict(_document("invoice", total_amount=12_000.0)) is UNKNOWN


def test_a_currency_the_parser_cannot_read_drops_the_amount_condition() -> None:
    named = DocumentAttributeCondition(attribute=DocumentAttribute.TOTAL_AMOUNT, at_least="10000", currency="Franken")
    unreadable = DocumentAttributeCondition(attribute=DocumentAttribute.TOTAL_AMOUNT, at_least="10000", currency="bits")

    assert (readable := named.readable()) is not None and readable.currency == "CHF"
    assert unreadable.readable() is None


def test_a_stored_date_covers_its_whole_precision() -> None:
    march = DocumentMetadataFilter(
        conditions=[_condition(DocumentAttribute.DATE, at_least="2025-03-10", at_most="2025-03-20")]
    )

    assert march.verdict(_document("invoice", date="2025-03-01", date_precision="month")) is MATCH
    assert march.verdict(_document("invoice", date="2025-03-01", date_precision="day")) is EXCLUDED
    assert march.verdict(_document("invoice", date="2025-01-01", date_precision="year")) is MATCH
    assert march.verdict(_document("invoice", date=None)) is UNKNOWN


def test_a_period_attribute_overlapping_the_range_matches() -> None:
    running_in_2025 = DocumentMetadataFilter(
        conditions=[_condition(DocumentAttribute.PERIOD, at_least="2025-01-01", at_most="2025-12-31")]
    )

    assert running_in_2025.verdict(_document("contract", period_start="2024-06-01", period_end="2026-05-31")) is MATCH
    assert (
        running_in_2025.verdict(_document("contract", period_start="2023-01-01", period_end="2023-12-31")) is EXCLUDED
    )
    assert running_in_2025.verdict(_document("contract", period_start="2025-04-01")) is MATCH


def test_the_request_period_applies_to_the_document_date() -> None:
    offers = DocumentMetadataFilter(types=[DocumentType.OFFER])
    year_2025 = PathDateRange(start=date(2025, 1, 1), end=date(2025, 12, 31))

    assert offers.verdict(_document("offer", date="2025-05-02", date_precision="day"), year_2025) is MATCH
    assert offers.verdict(_document("offer", date="2024-05-02", date_precision="day"), year_2025) is EXCLUDED
    assert offers.verdict(_document("offer", date=None), year_2025) is UNKNOWN


def test_one_exclusion_wins_over_an_unknown_part() -> None:
    hooli_contracts = DocumentMetadataFilter(
        types=[DocumentType.CONTRACT], conditions=[_condition(DocumentAttribute.PARTIES, contains="Hooli")]
    )

    assert hooli_contracts.verdict(_document("invoice", parties=None)) is EXCLUDED


@pytest.mark.parametrize(
    ("condition", "readable"),
    [
        (DocumentAttributeCondition(attribute=DocumentAttribute.ISSUER), False),
        (DocumentAttributeCondition(attribute=DocumentAttribute.ISSUER, contains="  "), False),
        (DocumentAttributeCondition(attribute=DocumentAttribute.DATE, contains="2025"), False),
        (DocumentAttributeCondition(attribute=DocumentAttribute.DATE, at_least="soon"), False),
        (DocumentAttributeCondition(attribute=DocumentAttribute.TOTAL_AMOUNT, at_least="5", at_most="1"), False),
        (DocumentAttributeCondition(attribute=DocumentAttribute.DATE, at_least="2025"), True),
        (DocumentAttributeCondition(attribute=DocumentAttribute.ISSUER, contains="Hooli"), True),
    ],
)
def test_a_condition_code_cannot_compare_is_dropped(condition: DocumentAttributeCondition, readable: bool) -> None:
    assert (condition.readable() is not None) is readable


def test_a_filter_of_nothing_readable_is_none() -> None:
    unreadable = DocumentAttributeCondition(attribute=DocumentAttribute.DATE, at_least="soon")

    assert DocumentMetadataFilter.of([], [unreadable]) is None
    assert DocumentMetadataFilter.of([DocumentType.INVOICE], [unreadable]) == DocumentMetadataFilter(
        types=[DocumentType.INVOICE]
    )


def test_counts_bound_their_examples() -> None:
    outcomes = [(f"folder/{index:03}.pdf", EXCLUDED) for index in range(30)] + [("kept.pdf", UNKNOWN)]

    counts = DocumentMetadataCounts.collect(outcomes)

    assert (counts.matched, counts.excluded, counts.unknown) == (0, 30, 1)
    assert len(counts.excluded_examples) == DocumentMetadataCounts.EXCLUDED_EXAMPLE_LIMIT
