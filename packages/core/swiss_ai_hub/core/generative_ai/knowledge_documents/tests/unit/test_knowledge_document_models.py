from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document import KnowledgeDocument
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.knowledge_documents.resolved_knowledge_collection import (
    ResolvedKnowledgeCollection,
)
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair

pytestmark = pytest.mark.unit

_RESOLVED = ResolvedKnowledgeCollection(
    collection=BucketNamespacePair(bucket_name="kb", namespace_name="finance"),
    db_name="kb",
    folder_name="Finanzen",
)


def _ref_doc(source: str, title: str | None = None, text: str = "", pages: int | None = None) -> SimpleNamespace:
    metadata = SimpleNamespace(source=source, document_title=title, number_of_pages=pages, updated_at=1735689600)
    return SimpleNamespace(id="abc123", data=SimpleNamespace(metadata=metadata, mimetype="text/plain", text=text))


def test_path_is_relative_to_the_folder_not_the_namespace_name() -> None:
    summary = KnowledgeDocumentSummary.from_ref_doc(
        _ref_doc("s3://kb/Finanzen/invoices/2025/acme.PDF", title="ACME invoice", pages=2), _RESOLVED
    )

    assert summary.path == "invoices/2025/acme.PDF"
    assert summary.filename == "acme.PDF"
    assert summary.file_type == "pdf"
    assert summary.title == "ACME invoice"
    assert summary.number_of_pages == 2
    assert summary.collection.namespace_name == "finance"
    assert summary.updated_at == datetime(2025, 1, 1, tzinfo=UTC)


def test_title_falls_back_to_the_filename_and_type_to_the_mimetype() -> None:
    summary = KnowledgeDocumentSummary.from_ref_doc(_ref_doc("s3://kb/Finanzen/README"), _RESOLVED)

    assert summary.title == "README"
    assert summary.file_type == "text/plain"


def test_document_at_the_top_of_the_folder() -> None:
    assert KnowledgeDocumentSummary.from_ref_doc(_ref_doc("s3://kb/Finanzen/notes.txt"), _RESOLVED).path == "notes.txt"


@pytest.mark.parametrize(
    ("start", "end", "expected_text", "expected_start", "expected_end"),
    [
        (None, None, "0123456789", 0, 10),
        (2, 5, "234", 2, 5),
        (8, None, "89", 8, 10),
        (None, 3, "012", 0, 3),
        (5, 500, "56789", 5, 10),
        (7, 3, "", 7, 7),
        (50, None, "", 10, 10),
    ],
)
def test_range_reads(
    start: int | None, end: int | None, expected_text: str, expected_start: int, expected_end: int
) -> None:
    document = KnowledgeDocument.from_ref_doc(
        _ref_doc("s3://kb/Finanzen/a.md", text="0123456789"), _RESOLVED, start, end
    )

    assert document.text == expected_text
    assert (document.start, document.end) == (expected_start, expected_end)
    assert document.text_length == 10
