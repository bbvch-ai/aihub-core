import asyncio
import json
from itertools import batched
from typing import Annotated

import grpc
from openai import OpenAIError
from pymilvus import MilvusException

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_collection_resolver import (
    KnowledgeCollectionResolver,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_listing import KnowledgeDocumentListing
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_reader import KnowledgeDocumentReader
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_search_budget import KnowledgeSearchBudget
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_semantic_match import KnowledgeSemanticMatch
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_semantic_passage import KnowledgeSemanticPassage
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_semantic_ranking import KnowledgeSemanticRanking
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_semantic_search_unavailable_error import (
    KnowledgeSemanticSearchUnavailableError,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.resolved_knowledge_collection import (
    ResolvedKnowledgeCollection,
)
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_model_config import EmbeddingModelConfig
from swiss_ai_hub.core.generative_ai.resources.models.llm.embedding_query_clamp import EmbeddingQueryClamp
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.generative_ai.retrievers.referenced_knowledge import ReferencedKnowledge
from swiss_ai_hub.core.infrastructure.litellm.lite_llm_service import LiteLLMService
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import DOCUMENT_ID, NAMESPACE
from swiss_ai_hub.core.persistence.rag.vectors.stores.document_passage_hit import DocumentPassageHit
from swiss_ai_hub.core.persistence.rag.vectors.stores.existing_milvus_vector_stores import ExistingMilvusVectorStores
from swiss_ai_hub.core.persistence.rag.vectors.stores.partition_aware_milvus_vector_store import (
    PartitionAwareMilvusVectorStore,
)

# Measured on Milvus 2.6: a filter naming 200,000 ids (5.4 MB) is accepted and costs under a second, so batches of
# 10,000 (270 kB) stay far from any limit, and a batch's remaining ids stay below Milvus' 16,384 hits per search.
IDS_PER_FILTER = 10_000
MAX_RANKED_DOCUMENTS = 1_000
# The usual constant of reciprocal rank fusion: it keeps the first few places of one ranking from outweighing the rest.
RECIPROCAL_RANK_CONSTANT = 60

type _Scope = tuple[str, str]
type _DocumentKey = tuple[str, str, str]
type _ModelRankings = dict[str, list[KnowledgeSemanticMatch]]


class KnowledgeSemanticSearch:
    """Ranks the documents of knowledge collections by meaning, independent of any agent.

    The chunk index has no path field, so a path restriction is resolved through the document listing into document
    ids, and the vector search is filtered to exactly those: the same documents the document tools see, never one
    outside the caller's globs, and never one still being ingested. Chunks are grouped by document in Milvus, so one
    long document cannot fill the ranking. Each database is searched with the embedding model it was indexed with;
    scores of one model are compared directly, while rankings of different models are merged by reciprocal rank fusion,
    since their similarities are not on one scale. A ranking is computed whole, once per call: one listing, one query
    embedding per model and one grouped search per database and batch of ids.

    Callers pass the collections the run may read, with the same trust rule as `KnowledgeDocumentReader`. Vector store
    and embedding model failures raise `KnowledgeSemanticSearchUnavailableError`.
    """

    @staticmethod
    @trace_fn
    async def rank(
        collections: Annotated[list[BucketNamespacePair], "Collections the caller may read; nothing else is searched"],
        query: Annotated[str, "What the documents are about, in words; ranked by meaning, not by exact terms"],
        *,
        path_globs: Annotated[list[str] | None, "Only documents whose path matches every one of these globs"] = None,
        passages_per_document: Annotated[int, "Closest chunks returned per document; text is most of the cost"] = 2,
        user: Annotated[UserIdentity | None, "Whose LiteLLM key embeds the query; the proxy's own when None"] = None,
        budget: Annotated[
            KnowledgeSearchBudget | None, "Deadline for the listing and every search; none when None"
        ] = None,
    ) -> KnowledgeSemanticRanking:
        if passages_per_document < 1:
            raise ValueError(f"passages_per_document must be positive, got {passages_per_document}")
        if not query.strip():
            raise ValueError("The query is empty; describe the documents in a few words.")
        listing = await KnowledgeDocumentReader.list_documents(collections, budget)
        for path_glob in path_globs or []:
            listing = listing.matching_glob(path_glob)
        if not listing.documents:
            return KnowledgeSemanticRanking(matches=[], documents_in_scope=0, unranked=0, capped=False)
        scopes = KnowledgeSemanticSearch._scopes(listing, await KnowledgeCollectionResolver.resolve_all(collections))
        try:
            by_model, with_passages = await KnowledgeSemanticSearch._rank_by_model(
                scopes, query, passages_per_document, user, budget
            )
        except (MilvusException, grpc.RpcError, OpenAIError) as ranking_error:
            raise KnowledgeSemanticSearchUnavailableError(ranking_error) from ranking_error
        matches = KnowledgeSemanticSearch._fused(list(by_model.values()))[:MAX_RANKED_DOCUMENTS]
        return KnowledgeSemanticRanking(
            matches=matches,
            documents_in_scope=listing.total,
            unranked=listing.total - with_passages,
            capped=with_passages > len(matches),
        )

    @staticmethod
    def _scopes(
        listing: KnowledgeDocumentListing, resolved: list[ResolvedKnowledgeCollection]
    ) -> dict[_Scope, dict[str, KnowledgeDocumentSummary]]:
        """The documents by the vector collection and namespace their chunks are stored under."""
        db_names = {
            (entry.collection.bucket_name, entry.collection.namespace_name): entry.db_name for entry in resolved
        }
        scopes: dict[_Scope, dict[str, KnowledgeDocumentSummary]] = {}
        for summary in listing.documents:
            collection = summary.collection
            key = (db_names[(collection.bucket_name, collection.namespace_name)], collection.namespace_name)
            scopes.setdefault(key, {})[summary.id] = summary
        return scopes

    @staticmethod
    async def _rank_by_model(
        scopes: dict[_Scope, dict[str, KnowledgeDocumentSummary]],
        query: str,
        passages_per_document: int,
        user: UserIdentity | None,
        budget: KnowledgeSearchBudget | None,
    ) -> tuple[_ModelRankings, int]:
        """Each embedding model's documents best first, and how many documents in scope have passages at all."""
        api_key = await LiteLLMService.api_key_for_user(user) if user else None
        embeddings: dict[str, list[float]] = {}
        by_model: _ModelRankings = {}
        with_passages = 0
        for (db_name, namespace), summaries in scopes.items():
            store = await asyncio.to_thread(ExistingMilvusVectorStores.find, db_name)
            if store is None:
                continue
            model_name = await asyncio.to_thread(ReferencedKnowledge.embedding_model_of, db_name)
            if model_name not in embeddings:
                embeddings[model_name] = await KnowledgeSemanticSearch._embed(query, model_name, api_key)
            hits, found = await KnowledgeSemanticSearch._rank_scope(
                store, namespace, list(summaries), embeddings[model_name], passages_per_document, budget
            )
            by_model.setdefault(model_name, []).extend(KnowledgeSemanticSearch._matches(hits, summaries))
            with_passages += found
        ordered = {
            model_name: sorted(matches, key=lambda match: (-match.score, match.summary.path))[:MAX_RANKED_DOCUMENTS]
            for model_name, matches in by_model.items()
        }
        return ordered, with_passages

    @staticmethod
    async def _embed(query: str, model_name: str, api_key: str | None) -> list[float]:
        embed_model, _ = EmbeddingModelConfig(model_name=model_name).to_llama_index(api_key=api_key)
        clamped = await asyncio.to_thread(EmbeddingQueryClamp.clamp, query, model_name=model_name)
        return await embed_model.aget_text_embedding(clamped)

    @staticmethod
    async def _rank_scope(
        store: PartitionAwareMilvusVectorStore,
        namespace: str,
        document_ids: list[str],
        embedding: list[float],
        passages_per_document: int,
        budget: KnowledgeSearchBudget | None,
    ) -> tuple[list[DocumentPassageHit], int]:
        """The best documents of one namespace, one filtered search per batch of ids, and how many have passages."""
        hits: list[DocumentPassageHit] = []
        with_passages = 0
        for batch in batched(document_ids, IDS_PER_FILTER):
            batch_hits, batch_with_passages = await KnowledgeSemanticSearch._rank_batch(
                store, namespace, list(batch), embedding, passages_per_document, budget
            )
            hits.extend(batch_hits)
            with_passages += batch_with_passages
        return hits, with_passages

    @staticmethod
    async def _rank_batch(
        store: PartitionAwareMilvusVectorStore,
        namespace: str,
        batch: list[str],
        embedding: list[float],
        passages_per_document: int,
        budget: KnowledgeSearchBudget | None,
    ) -> tuple[list[DocumentPassageHit], int]:
        """A search that returns fewer documents than it asked for has found every one with passages; only when it is
        cut are the rest checked, by id and without text, to tell documents beyond the cut from those without vectors.
        """
        limit = min(len(batch), MAX_RANKED_DOCUMENTS)
        hits = await asyncio.to_thread(
            store.passages_grouped_by_document,
            embedding,
            [namespace],
            KnowledgeSemanticSearch._filter(namespace, batch),
            limit,
            passages_per_document,
            KnowledgeSemanticSearch._timeout(budget),
        )
        ranked = {hit.document_id for hit in hits}
        rest = [document_id for document_id in batch if document_id not in ranked]
        if len(ranked) < limit or not rest:
            return hits, len(ranked)
        beyond = await asyncio.to_thread(
            store.documents_with_passages,
            embedding,
            [namespace],
            KnowledgeSemanticSearch._filter(namespace, rest),
            len(rest),
            KnowledgeSemanticSearch._timeout(budget),
        )
        return hits, len(ranked) + len(beyond)

    @staticmethod
    def _filter(namespace: str, document_ids: list[str]) -> str:
        return f"{NAMESPACE} == {json.dumps(namespace)} and {DOCUMENT_ID} in {json.dumps(document_ids)}"

    @staticmethod
    def _timeout(budget: KnowledgeSearchBudget | None) -> float | None:
        return budget.remaining_seconds() if budget else None

    @staticmethod
    def _matches(
        hits: list[DocumentPassageHit], summaries: dict[str, KnowledgeDocumentSummary]
    ) -> list[KnowledgeSemanticMatch]:
        passages: dict[str, list[KnowledgeSemanticPassage]] = {}
        for hit in hits:
            passages.setdefault(hit.document_id, []).append(KnowledgeSemanticPassage(text=hit.text, score=hit.score))
        return [
            KnowledgeSemanticMatch(
                summary=summaries[document_id],
                score=max(passage.score for passage in found),
                passages=sorted(found, key=lambda passage: -passage.score),
            )
            for document_id, found in passages.items()
        ]

    @staticmethod
    def _fused(rankings: list[list[KnowledgeSemanticMatch]]) -> list[KnowledgeSemanticMatch]:
        """Reciprocal rank fusion: a document's place in its own model's ranking counts, never its raw score."""
        fused: dict[_DocumentKey, float] = {}
        matches: dict[_DocumentKey, KnowledgeSemanticMatch] = {}
        for ranking in rankings:
            for position, match in enumerate(ranking, start=1):
                key = KnowledgeSemanticSearch._key(match)
                fused[key] = fused.get(key, 0.0) + 1 / (RECIPROCAL_RANK_CONSTANT + position)
                matches[key] = match
        return sorted(
            matches.values(),
            key=lambda match: (-fused[KnowledgeSemanticSearch._key(match)], match.summary.path),
        )

    @staticmethod
    def _key(match: KnowledgeSemanticMatch) -> _DocumentKey:
        collection = match.summary.collection
        return collection.bucket_name, collection.namespace_name, match.summary.id
