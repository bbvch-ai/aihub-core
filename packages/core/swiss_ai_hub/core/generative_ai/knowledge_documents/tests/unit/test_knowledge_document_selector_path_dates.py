from datetime import UTC, date, datetime

import pytest

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
_PATHS = [
    "invoices/2024/acme-1.pdf",
    "invoices/2025/acme-2.pdf",
    "invoices/2025/globex-3.pdf",
    "invoices/2026/acme-4.pdf",
    "invoices/acme-undated.pdf",
    "other/2024/report.pdf",
]
_YEAR_2025 = PathDateRange(start=date(2025, 1, 1), end=date(2025, 12, 31))


def _summary(path: str) -> KnowledgeDocumentSummary:
    filename = path.rsplit("/", 1)[-1]
    return KnowledgeDocumentSummary(
        id=path,
        collection=_FINANCE,
        path=path,
        filename=filename,
        title=filename,
        file_type="pdf",
        updated_at=datetime(2025, 1, 1, tzinfo=UTC),
    )


@pytest.fixture(autouse=True)
def _listing(monkeypatch: pytest.MonkeyPatch) -> None:
    async def list_documents(
        collections: list[BucketNamespacePair], budget: KnowledgeSearchBudget
    ) -> KnowledgeDocumentListing:
        return KnowledgeDocumentListing.from_summaries([_summary(path) for path in _PATHS])

    monkeypatch.setattr(KnowledgeDocumentReader, "list_documents", list_documents)


def _acme_or_2024(path_date_range: PathDateRange | None) -> KnowledgeDocumentSelection:
    return KnowledgeDocumentSelection(
        any_of=[KnowledgeDocumentCriteria(path_regex="acme"), KnowledgeDocumentCriteria(path_glob="other/**")],
        path_date_range=path_date_range,
    )


@pytest.mark.asyncio
async def test_the_period_filters_the_union_of_the_entries() -> None:
    result = await KnowledgeDocumentSelector.resolve([_FINANCE], _acme_or_2024(_YEAR_2025), limit=10)

    assert [document.path for document in result.documents] == [
        "invoices/2025/acme-2.pdf",
        "invoices/acme-undated.pdf",
    ]
    assert result.path_dates is not None
    assert (result.path_dates.in_range, result.path_dates.excluded, result.path_dates.undated) == (1, 3, 1)


@pytest.mark.asyncio
async def test_only_documents_the_entries_selected_count_as_excluded() -> None:
    result = await KnowledgeDocumentSelector.resolve([_FINANCE], _acme_or_2024(_YEAR_2025), limit=10)

    assert result.path_dates is not None
    assert result.path_dates.excluded_examples == [
        "invoices/2024/acme-1.pdf",
        "invoices/2026/acme-4.pdf",
        "other/2024/report.pdf",
    ]
    assert result.path_dates.outside_years == [2024, 2026]


@pytest.mark.asyncio
async def test_the_limit_applies_after_the_period() -> None:
    selection = KnowledgeDocumentSelection(
        any_of=[KnowledgeDocumentCriteria(path_glob="invoices/**")], path_date_range=_YEAR_2025
    )

    result = await KnowledgeDocumentSelector.resolve([_FINANCE], selection, limit=2)

    assert [document.path for document in result.documents] == [
        "invoices/2025/acme-2.pdf",
        "invoices/2025/globex-3.pdf",
    ]
    assert result.truncated is True


@pytest.mark.asyncio
async def test_without_a_period_the_selection_resolves_as_before() -> None:
    result = await KnowledgeDocumentSelector.resolve([_FINANCE], _acme_or_2024(None), limit=10)

    assert [document.path for document in result.documents] == [
        "invoices/2024/acme-1.pdf",
        "invoices/2025/acme-2.pdf",
        "invoices/2026/acme-4.pdf",
        "invoices/acme-undated.pdf",
        "other/2024/report.pdf",
    ]
    assert result.path_dates is None
