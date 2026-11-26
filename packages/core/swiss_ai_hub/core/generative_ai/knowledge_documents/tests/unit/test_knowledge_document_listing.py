from datetime import UTC, date, datetime

import pytest

from swiss_ai_hub.core.generative_ai.knowledge_documents.invalid_path_pattern_error import InvalidPathPatternError
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_criteria import KnowledgeDocumentCriteria
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_listing import KnowledgeDocumentListing
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_date_range import PathDateRange
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair

pytestmark = pytest.mark.unit

_FINANCE = BucketNamespacePair(bucket_name="kb", namespace_name="finance")
_LEGAL = BucketNamespacePair(bucket_name="kb", namespace_name="legal")
_HR = BucketNamespacePair(bucket_name="hr", namespace_name="people")


def _summary(collection: BucketNamespacePair, path: str) -> KnowledgeDocumentSummary:
    filename = path.rsplit("/", 1)[-1]
    return KnowledgeDocumentSummary(
        id=path,
        collection=collection,
        collection_name=f"{collection.bucket_name}/{collection.namespace_name}",
        path=path,
        filename=filename,
        title=filename,
        file_type=filename.rsplit(".", 1)[-1].lower(),
        updated_at=datetime(2025, 1, 1, tzinfo=UTC),
    )


@pytest.fixture
def listing() -> KnowledgeDocumentListing:
    return KnowledgeDocumentListing.from_summaries(
        [
            _summary(_LEGAL, "contracts/2025/msa-acme.md"),
            _summary(_FINANCE, "invoices/2025/q2/acme-0002.PDF"),
            _summary(_FINANCE, "invoices/2024/acme-0099.pdf"),
            _summary(_FINANCE, "invoices/2025/q1/acme-0001.pdf"),
            _summary(_FINANCE, "invoices/2025/globex-0003.pdf"),
            _summary(_HR, "invoices/2025/q1/acme-0001.pdf"),
        ]
    )


def _keys(listing: KnowledgeDocumentListing) -> list[tuple[str, str, str]]:
    return [(doc.collection.bucket_name, doc.collection.namespace_name, doc.path) for doc in listing.documents]


def test_documents_are_sorted_by_database_collection_and_path(listing: KnowledgeDocumentListing) -> None:
    assert _keys(listing) == [
        ("hr", "people", "invoices/2025/q1/acme-0001.pdf"),
        ("kb", "finance", "invoices/2024/acme-0099.pdf"),
        ("kb", "finance", "invoices/2025/globex-0003.pdf"),
        ("kb", "finance", "invoices/2025/q1/acme-0001.pdf"),
        ("kb", "finance", "invoices/2025/q2/acme-0002.PDF"),
        ("kb", "legal", "contracts/2025/msa-acme.md"),
    ]
    assert listing.total == 6
    assert listing.model_dump()["total"] == 6


def test_glob_then_regex_narrow_without_touching_the_original(listing: KnowledgeDocumentListing) -> None:
    narrowed = listing.matching_glob("invoices/2025/**/*.pdf").matching_regex("acme")

    assert _keys(narrowed) == [
        ("hr", "people", "invoices/2025/q1/acme-0001.pdf"),
        ("kb", "finance", "invoices/2025/q1/acme-0001.pdf"),
        ("kb", "finance", "invoices/2025/q2/acme-0002.PDF"),
    ]
    assert narrowed.total == 3
    assert listing.total == 6


def test_no_match_is_an_empty_listing(listing: KnowledgeDocumentListing) -> None:
    empty = listing.matching_glob("nothing/**")

    assert empty.documents == []
    assert empty.total == 0


def test_invalid_pattern_fails_the_filter(listing: KnowledgeDocumentListing) -> None:
    with pytest.raises(InvalidPathPatternError):
        listing.matching_regex("invoices/(2025")


def test_a_collection_name_keeps_only_that_collections_documents(listing: KnowledgeDocumentListing) -> None:
    assert [doc.path for doc in listing.in_collection("kb/legal").documents] == ["contracts/2025/msa-acme.md"]
    assert listing.in_collection("kb/legal/contracts").documents == []


def test_a_period_keeps_every_document_not_dated_outside_it_in_order(listing: KnowledgeDocumentListing) -> None:
    kept, counts = listing.dated_within(PathDateRange(start=date(2025, 1, 1), end=date(2025, 3, 31)))

    assert _keys(kept) == [
        ("hr", "people", "invoices/2025/q1/acme-0001.pdf"),
        ("kb", "finance", "invoices/2025/globex-0003.pdf"),
        ("kb", "finance", "invoices/2025/q1/acme-0001.pdf"),
        ("kb", "legal", "contracts/2025/msa-acme.md"),
    ]
    assert (counts.in_range, counts.excluded, counts.undated) == (4, 2, 0)
    assert counts.excluded_examples == ["invoices/2024/acme-0099.pdf", "invoices/2025/q2/acme-0002.PDF"]
    assert counts.outside_years == [2024, 2025]
    assert listing.total == 6


def test_the_criteria_offer_no_year_to_select_by() -> None:
    fields = KnowledgeDocumentCriteria.model_fields
    descriptions = [fields["path_glob"].description or "", fields["content_query"].description or ""]

    assert not any("2025" in description or "year" in description for description in descriptions)
