"""Semantic ranking stays within the caller's globs, fuses embedding models by rank, and says what it leaves out."""

import json
import re
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from openai import APIConnectionError
from pymilvus import MilvusException

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_listing import KnowledgeDocumentListing
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_search_budget import KnowledgeSearchBudget
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_semantic_ranking import KnowledgeSemanticRanking
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_semantic_search import KnowledgeSemanticSearch
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_semantic_search_unavailable_error import (
    KnowledgeSemanticSearchUnavailableError,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.resolved_knowledge_collection import (
    ResolvedKnowledgeCollection,
)
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.persistence.rag.vectors.stores.document_passage_hit import DocumentPassageHit

MODULE = "swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_semantic_search"
LEGAL = BucketNamespacePair(bucket_name="legal-bucket", namespace_name="legal")
VERTRAG = BucketNamespacePair(bucket_name="vertrag-bucket", namespace_name="vertrag")
RESOLVED = [
    ResolvedKnowledgeCollection(collection=LEGAL, db_name="legaldb", folder_name="legal"),
    ResolvedKnowledgeCollection(collection=VERTRAG, db_name="vertragdb", folder_name="vertrag"),
]
MODELS = {"legaldb": "embedding/bge-m3", "vertragdb": "embedding/e5"}


def _summary(document_id: str, path: str, collection: BucketNamespacePair = LEGAL) -> KnowledgeDocumentSummary:
    return KnowledgeDocumentSummary(
        id=document_id,
        collection=collection,
        path=path,
        filename=path.rsplit("/", 1)[-1],
        title=path,
        file_type="md",
        updated_at=datetime(2025, 1, 1, tzinfo=UTC),
    )


CONTRACTS = [
    _summary("c1", "contracts/a.md"),
    _summary("c2", "contracts/b.md"),
    _summary("c3", "contracts/c.md"),
    _summary("o1", "other/secret.md"),
]


class _Store:
    """Answers like Milvus: only ids the filter names that have vectors, best first, two passages each."""

    def __init__(self, scores: dict[str, float], failure: Exception | None = None) -> None:
        self.scores = scores
        self.failure = failure
        self.expressions: list[str] = []
        self.existence_checks: list[list[str]] = []
        self.timeouts: list[float | None] = []

    def _named(self, expression: str) -> list[str]:
        return [name for name in json.loads(re.search(r"in (\[.*\])$", expression).group(1)) if name in self.scores]

    def passages_grouped_by_document(
        self, embedding: list[float], namespaces: list[str], expression: str, documents: int, passages: int, timeout
    ) -> list[DocumentPassageHit]:
        if self.failure:
            raise self.failure
        self.expressions.append(expression)
        self.timeouts.append(timeout)
        ranked = sorted(self._named(expression), key=lambda document_id: -self.scores[document_id])[:documents]
        return [
            DocumentPassageHit(
                document_id=document_id, text=f"{document_id} passage {index}", score=self.scores[document_id]
            )
            for document_id in ranked
            for index in range(passages)
        ]

    def documents_with_passages(
        self, embedding: list[float], namespaces: list[str], expression: str, documents: int, timeout
    ) -> set[str]:
        self.existence_checks.append(json.loads(re.search(r"in (\[.*\])$", expression).group(1)))
        return set(self._named(expression)[:documents])


async def _rank(
    stores: dict[str, _Store | None],
    summaries: list[KnowledgeDocumentSummary],
    embedding_failure: Exception | None = None,
    **kwargs: Any,
) -> KnowledgeSemanticRanking:
    embed = AsyncMock(side_effect=embedding_failure) if embedding_failure else AsyncMock(return_value=[0.1, 0.2])
    with (
        patch(
            f"{MODULE}.KnowledgeDocumentReader.list_documents",
            AsyncMock(return_value=KnowledgeDocumentListing.from_summaries(summaries)),
        ),
        patch(f"{MODULE}.KnowledgeCollectionResolver.resolve_all", AsyncMock(return_value=RESOLVED)),
        patch(f"{MODULE}.ReferencedKnowledge.embedding_model_of", side_effect=MODELS.__getitem__),
        patch(f"{MODULE}.KnowledgeSemanticSearch._embed", embed),
        patch(f"{MODULE}.ExistingMilvusVectorStores.find", side_effect=stores.__getitem__),
    ):
        return await KnowledgeSemanticSearch.rank([LEGAL, VERTRAG], "liability", **kwargs)


def _ids(ranking: KnowledgeSemanticRanking) -> list[str]:
    return [match.summary.id for match in ranking.matches]


@pytest.mark.asyncio
async def test_a_document_outside_the_glob_is_never_ranked_however_close_it_is():
    store = _Store({"c1": 0.9, "c2": 0.4, "c3": 0.7, "o1": 0.99})

    ranking = await _rank({"legaldb": store}, CONTRACTS, path_globs=["contracts/**"])

    assert _ids(ranking) == ["c1", "c3", "c2"]
    assert all('"o1"' not in expression for expression in store.expressions)
    assert (ranking.documents_in_scope, ranking.unranked, ranking.capped) == (3, 0, False)
    assert ranking.matches[0].passages[0].text == "c1 passage 0"


@pytest.mark.asyncio
async def test_a_scope_larger_than_one_filter_is_searched_in_batches_and_merged():
    store = _Store({"c1": 0.9, "c2": 0.4, "c3": 0.7})

    with patch(f"{MODULE}.IDS_PER_FILTER", 2):
        ranking = await _rank({"legaldb": store}, CONTRACTS, path_globs=["contracts/**"])

    assert len(store.expressions) == 2
    assert _ids(ranking) == ["c1", "c3", "c2"]


@pytest.mark.asyncio
async def test_two_embedding_models_are_merged_by_their_ranks_not_their_raw_scores():
    """The second model scores everything lower; by raw score both its documents would come last."""
    legal = _Store({"c1": 0.9, "c2": 0.85})
    vertrag = _Store({"v1": 0.31, "v2": 0.2})
    summaries = [*CONTRACTS[:2], _summary("v1", "vertrag/x.md", VERTRAG), _summary("v2", "vertrag/y.md", VERTRAG)]

    ranking = await _rank({"legaldb": legal, "vertragdb": vertrag}, summaries)

    assert _ids(ranking) == ["c1", "v1", "c2", "v2"]


@pytest.mark.asyncio
async def test_documents_without_vectors_are_counted_as_unranked():
    store = _Store({"c1": 0.9, "c3": 0.7})

    ranking = await _rank({"legaldb": store}, CONTRACTS, path_globs=["contracts/**"])

    assert _ids(ranking) == ["c1", "c3"]
    assert (ranking.documents_in_scope, ranking.unranked, ranking.capped) == (3, 1, False)
    assert store.existence_checks == []


@pytest.mark.asyncio
async def test_a_cut_ranking_says_so_and_still_tells_the_documents_without_vectors_apart():
    store = _Store({"c1": 0.9, "c2": 0.4, "c3": 0.7})

    with patch(f"{MODULE}.MAX_RANKED_DOCUMENTS", 2):
        ranking = await _rank({"legaldb": store}, CONTRACTS)

    assert _ids(ranking) == ["c1", "c3"]
    assert store.existence_checks == [["c2", "o1"]]
    assert (ranking.documents_in_scope, ranking.unranked, ranking.capped) == (4, 1, True)


@pytest.mark.asyncio
async def test_a_database_without_a_collection_has_nothing_ranked():
    ranking = await _rank({"legaldb": None}, CONTRACTS)

    assert ranking.matches == []
    assert (ranking.documents_in_scope, ranking.unranked, ranking.capped) == (4, 4, False)


@pytest.mark.asyncio
async def test_a_vector_store_failure_is_reported_as_unavailable():
    store = _Store({}, failure=MilvusException(code=2, message="Fail connecting to server"))

    with pytest.raises(KnowledgeSemanticSearchUnavailableError, match="Fail connecting"):
        await _rank({"legaldb": store}, CONTRACTS)


@pytest.mark.asyncio
async def test_a_query_the_embedding_model_cannot_embed_is_reported_as_unavailable():
    failure = APIConnectionError(request=httpx.Request("POST", "http://litellm/embeddings"))

    with pytest.raises(KnowledgeSemanticSearchUnavailableError, match="Connection error"):
        await _rank({"legaldb": _Store({"c1": 0.9})}, CONTRACTS, embedding_failure=failure)


@pytest.mark.asyncio
async def test_each_search_gets_what_is_left_of_the_budget():
    store = _Store({"c1": 0.9})

    await _rank({"legaldb": store}, CONTRACTS, budget=KnowledgeSearchBudget(20))

    assert store.timeouts and all(0 < timeout <= 20 for timeout in store.timeouts)


@pytest.mark.asyncio
async def test_an_empty_query_is_refused():
    with pytest.raises(ValueError, match="empty"):
        await KnowledgeSemanticSearch.rank([LEGAL], "  ")


def test_ranks_of_one_model_keep_their_order():
    matches = [MagicMock(summary=_summary(name, f"{name}.md"), score=score) for name, score in [("b", 0.9), ("a", 0.8)]]

    assert [match.summary.id for match in KnowledgeSemanticSearch._fused([matches])] == ["b", "a"]
