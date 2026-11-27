from datetime import UTC, date, datetime

import pytest

from swiss_ai_hub.core.generative_ai.document.classification.document_type import DocumentType
from swiss_ai_hub.core.generative_ai.knowledge_documents.document_metadata_filter import DocumentMetadataFilter
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_criteria import KnowledgeDocumentCriteria
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_listing import KnowledgeDocumentListing
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_reader import KnowledgeDocumentReader
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_selection import (
    KnowledgeDocumentSelection,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_selector import KnowledgeDocumentSelector
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_search_budget import KnowledgeSearchBudget
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_date_range import PathDateRange
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair

pytestmark = pytest.mark.unit

_FINANCE = BucketNamespacePair(bucket_name="kb", namespace_name="finance")
_DOCUMENTS = [
    ("2024/offer-a.pdf", "offer", "2024-11-03"),
    ("2025/offer-b.pdf", "offer", "2024-12-30"),
    ("2025/offer-c.pdf", "offer", "2025-02-14"),
    ("2025/invoice-d.pdf", "invoice", "2025-03-01"),
    ("2025/unclassified-e.pdf", None, None),
    ("undated/offer-f.pdf", "offer", None),
]


def _summary(path: str, document_type: str | None, issued: str | None) -> KnowledgeDocumentSummary:
    return KnowledgeDocumentSummary(
        id=path,
        collection=_FINANCE,
        path=path,
        filename=path.rsplit("/", 1)[-1],
        title=path,
        file_type="pdf",
        updated_at=datetime(2025, 1, 1, tzinfo=UTC),
        document_type=document_type,
        document_types=[document_type] if document_type else [],
        document_attributes={"document_date": issued, "document_date_precision": "day" if issued else None},
    )


@pytest.fixture(autouse=True)
def _listing(monkeypatch: pytest.MonkeyPatch) -> None:
    async def list_documents(
        collections: list[BucketNamespacePair], budget: KnowledgeSearchBudget
    ) -> KnowledgeDocumentListing:
        return KnowledgeDocumentListing.from_summaries([_summary(*document) for document in _DOCUMENTS])

    monkeypatch.setattr(KnowledgeDocumentReader, "list_documents", list_documents)


def _selection(
    metadata_filter: DocumentMetadataFilter | None, period: PathDateRange | None = None
) -> KnowledgeDocumentSelection:
    return KnowledgeDocumentSelection(
        any_of=[KnowledgeDocumentCriteria()], path_date_range=period, metadata_filter=metadata_filter
    )


@pytest.mark.asyncio
async def test_without_a_filter_the_selection_is_unchanged() -> None:
    result = await KnowledgeDocumentSelector.resolve([_FINANCE], _selection(None), limit=10)

    assert len(result.documents) == len(_DOCUMENTS)
    assert result.metadata is None


@pytest.mark.asyncio
async def test_a_type_keeps_its_documents_and_the_unclassified_ones() -> None:
    result = await KnowledgeDocumentSelector.resolve(
        [_FINANCE], _selection(DocumentMetadataFilter(types=[DocumentType.OFFER])), limit=10
    )

    assert [document.path for document in result.documents] == [
        "2024/offer-a.pdf",
        "2025/offer-b.pdf",
        "2025/offer-c.pdf",
        "2025/unclassified-e.pdf",
        "undated/offer-f.pdf",
    ]
    assert result.metadata is not None
    assert (result.metadata.matched, result.metadata.excluded, result.metadata.unknown) == (4, 1, 1)
    assert result.metadata.excluded_examples == ["2025/invoice-d.pdf"]


@pytest.mark.asyncio
async def test_the_period_applies_to_the_path_and_then_to_the_document_date() -> None:
    year_2025 = PathDateRange(start=date(2025, 1, 1), end=date(2025, 12, 31))

    result = await KnowledgeDocumentSelector.resolve(
        [_FINANCE], _selection(DocumentMetadataFilter(types=[DocumentType.OFFER]), year_2025), limit=10
    )

    assert [document.path for document in result.documents] == [
        "2025/offer-c.pdf",
        "2025/unclassified-e.pdf",
        "undated/offer-f.pdf",
    ]
    assert result.path_dates is not None and result.path_dates.excluded == 1
    assert result.metadata is not None
    assert (result.metadata.matched, result.metadata.excluded, result.metadata.unknown) == (1, 2, 2)


@pytest.mark.asyncio
async def test_the_limit_counts_what_the_filter_keeps() -> None:
    result = await KnowledgeDocumentSelector.resolve(
        [_FINANCE], _selection(DocumentMetadataFilter(types=[DocumentType.INVOICE])), limit=1
    )

    assert [document.path for document in result.documents] == ["2025/invoice-d.pdf"]
    assert result.truncated
