"""Semantic search ranks only the documents a caller's globs allow, by id, in batches, and pages over the ranking."""

import json
import re
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_listing import KnowledgeDocumentListing
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_semantic_search import KnowledgeSemanticSearch
from swiss_ai_hub.core.generative_ai.knowledge_documents.resolved_knowledge_collection import (
    ResolvedKnowledgeCollection,
)
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.persistence.rag.vectors.stores.document_passage_hit import DocumentPassageHit

MODULE = "swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_semantic_search"
LEGAL = BucketNamespacePair(bucket_name="legal-bucket", namespace_name="legal")
SCORES = {"c1": 0.9, "c2": 0.4, "c3": 0.7, "o1": 0.99}


def _summary(document_id: str, path: str) -> KnowledgeDocumentSummary:
    return KnowledgeDocumentSummary(
        id=document_id,
        collection=LEGAL,
        path=path,
        filename=path.rsplit("/", 1)[-1],
        title=path,
        file_type="md",
        updated_at=datetime(2025, 1, 1, tzinfo=UTC),
    )


LISTING = KnowledgeDocumentListing.from_summaries(
    [
        _summary("c1", "contracts/a.md"),
        _summary("c2", "contracts/b.md"),
        _summary("c3", "contracts/c.md"),
        _summary("o1", "other/secret.md"),
    ]
)


class _Store:
    """Answers like Milvus: only ids the filter names, best first, two passages each."""

    def __init__(self) -> None:
        self.expressions: list[str] = []

    def passages_grouped_by_document(
        self, embedding: list[float], namespaces: list[str], expression: str, documents: int, passages: int
    ) -> list[DocumentPassageHit]:
        self.expressions.append(expression)
        named = json.loads(re.search(r"in (\[.*\])$", expression).group(1))
        ranked = sorted(named, key=lambda document_id: -SCORES[document_id])[:documents]
        return [
            DocumentPassageHit(
                document_id=document_id, text=f"{document_id} passage {index}", score=SCORES[document_id]
            )
            for document_id in ranked
            for index in range(2)
        ]


async def _search(store: _Store, **kwargs: Any):
    resolved = [ResolvedKnowledgeCollection(collection=LEGAL, db_name="legaldb", folder_name="legal")]
    config = MagicMock()
    config.return_value.to_llama_index.return_value = store
    with (
        patch(f"{MODULE}.KnowledgeDocumentReader.list_documents", AsyncMock(return_value=LISTING)),
        patch(f"{MODULE}.KnowledgeCollectionResolver.resolve_all", AsyncMock(return_value=resolved)),
        patch(f"{MODULE}.ReferencedKnowledge.embedding_model_of", return_value="embedding/bge-m3"),
        patch(f"{MODULE}.KnowledgeSemanticSearch._embed", AsyncMock(return_value=[0.1, 0.2])),
        patch(f"{MODULE}.MilvusVectorStoreConfig", config),
    ):
        return await KnowledgeSemanticSearch.search([LEGAL], "liability", **kwargs)


@pytest.mark.asyncio
async def test_a_document_outside_the_glob_is_never_ranked_however_close_it_is():
    store = _Store()

    result = await _search(store, path_globs=["contracts/**"])

    assert [match.summary.id for match in result.matches] == ["c1", "c3", "c2"]
    assert all('"o1"' not in expression for expression in store.expressions)
    assert result.documents_in_scope == 3
    assert result.matches[0].passages[0].text == "c1 passage 0"


@pytest.mark.asyncio
async def test_a_scope_larger_than_one_filter_is_searched_in_batches_and_merged():
    store = _Store()

    with patch(f"{MODULE}.IDS_PER_FILTER", 2):
        result = await _search(store, path_globs=["contracts/**"])

    assert len(store.expressions) == 2
    assert [match.summary.id for match in result.matches] == ["c1", "c3", "c2"]


@pytest.mark.asyncio
async def test_pages_follow_the_ranking_and_say_where_it_continues():
    first = await _search(_Store(), path_globs=["contracts/**"], limit=2)
    second = await _search(_Store(), path_globs=["contracts/**"], limit=2, offset=2)

    assert [match.summary.id for match in first.matches] == ["c1", "c3"]
    assert first.next_offset == 2
    assert [match.summary.id for match in second.matches] == ["c2"]
    assert second.next_offset is None


@pytest.mark.asyncio
async def test_an_empty_query_is_refused():
    with pytest.raises(ValueError, match="empty"):
        await KnowledgeSemanticSearch.search([LEGAL], "  ")
