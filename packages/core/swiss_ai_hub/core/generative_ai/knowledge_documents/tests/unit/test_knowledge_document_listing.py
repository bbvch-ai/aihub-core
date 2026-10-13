from datetime import UTC, datetime

import pytest

from swiss_ai_hub.core.generative_ai.knowledge_documents.invalid_path_pattern_error import InvalidPathPatternError
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_listing import KnowledgeDocumentListing
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
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
