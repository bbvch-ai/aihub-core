import asyncio
import json
from itertools import batched
from typing import Annotated

from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_collection_resolver import (
    KnowledgeCollectionResolver,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_listing import KnowledgeDocumentListing
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_reader import KnowledgeDocumentReader
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_semantic_match import KnowledgeSemanticMatch
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_semantic_passage import KnowledgeSemanticPassage
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_semantic_search_result import (
    KnowledgeSemanticSearchResult,
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
from swiss_ai_hub.core.persistence.rag.vectors.stores.milvus_vector_store_config import MilvusVectorStoreConfig

# Measured on Milvus 2.6: a filter naming 200,000 ids (5.4 MB) is accepted and costs under a second, so batches of
# 10,000 (270 kB) stay far from any limit while a scope of 100,000 documents needs ten searches, not a truncation.
IDS_PER_FILTER = 10_000
# Milvus caps a search at 16,384 hits, and a grouped search returns up to `passages_per_document` hits per document.
MAX_RANKED_DOCUMENTS = 1_000

type _Group = tuple[str, str]


class KnowledgeSemanticSearch:
    """Ranks the documents of knowledge collections by meaning, a page at a time, independent of any agent.

    The chunk index has no path field, so a path restriction is resolved through the document listing into document
    ids, and the vector search is filtered to exactly those: the same documents the document tools see, never one
    outside the caller's globs, and never one still being ingested. Each database is searched with the embedding model
    it was indexed with, and chunks are grouped by document in Milvus, so one long document cannot fill the ranking.

    Callers pass the collections the run may read, with the same trust rule as `KnowledgeDocumentReader`.
    """

    @staticmethod
    @trace_fn
    async def search(
        collections: Annotated[list[BucketNamespacePair], "Collections the caller may read; nothing else is searched"],
        query: Annotated[str, "What the documents are about, in words; ranked by meaning, not by exact terms"],
        *,
        path_globs: Annotated[list[str] | None, "Only documents whose path matches every one of these globs"] = None,
        offset: Annotated[int, "Position in the ranking of the first document to return"] = 0,
        limit: Annotated[int, "Documents per page"] = 15,
        passages_per_document: Annotated[int, "Closest chunks returned per document"] = 5,
        user: Annotated[UserIdentity | None, "Whose LiteLLM key embeds the query; the proxy's own when None"] = None,
    ) -> KnowledgeSemanticSearchResult:
        if offset < 0 or limit < 1:
            raise ValueError(f"offset must not be negative and limit must be positive, got {offset} and {limit}")
        if not query.strip():
            raise ValueError("The query is empty; describe the documents in a few words.")
        listing = await KnowledgeDocumentReader.list_documents(collections)
        for path_glob in path_globs or []:
            listing = listing.matching_glob(path_glob)
        end = min(offset + limit, MAX_RANKED_DOCUMENTS)
        if offset >= end or not listing.documents:
            return KnowledgeSemanticSearchResult(matches=[], documents_in_scope=listing.total, next_offset=None)
        groups = KnowledgeSemanticSearch._groups(listing, await KnowledgeCollectionResolver.resolve_all(collections))
        api_key = await LiteLLMService.api_key_for_user(user) if user else None
        embeddings: dict[str, list[float]] = {}
        ranked: list[KnowledgeSemanticMatch] = []
        for (db_name, namespace), summaries in groups.items():
            model_name = await asyncio.to_thread(ReferencedKnowledge.embedding_model_of, db_name)
            if model_name not in embeddings:
                embeddings[model_name] = await KnowledgeSemanticSearch._embed(query, model_name, api_key)
            ranked.extend(
                await KnowledgeSemanticSearch._rank(
                    db_name, namespace, summaries, embeddings[model_name], end, passages_per_document
                )
            )
        ranked.sort(key=lambda match: (-match.score, match.summary.path))
        more = end < min(listing.total, MAX_RANKED_DOCUMENTS) and len(ranked) >= end
        return KnowledgeSemanticSearchResult(
            matches=ranked[offset:end], documents_in_scope=listing.total, next_offset=end if more else None
        )

    @staticmethod
    def _groups(
        listing: KnowledgeDocumentListing, resolved: list[ResolvedKnowledgeCollection]
    ) -> dict[_Group, dict[str, KnowledgeDocumentSummary]]:
        """The documents by the vector collection and namespace their chunks are stored under."""
        db_names = {
            (entry.collection.bucket_name, entry.collection.namespace_name): entry.db_name for entry in resolved
        }
        groups: dict[_Group, dict[str, KnowledgeDocumentSummary]] = {}
        for summary in listing.documents:
            collection = summary.collection
            key = (db_names[(collection.bucket_name, collection.namespace_name)], collection.namespace_name)
            groups.setdefault(key, {})[summary.id] = summary
        return groups

    @staticmethod
    async def _embed(query: str, model_name: str, api_key: str | None) -> list[float]:
        embed_model, _ = EmbeddingModelConfig(model_name=model_name).to_llama_index(api_key=api_key)
        clamped = await asyncio.to_thread(EmbeddingQueryClamp.clamp, query, model_name=model_name)
        return await embed_model.aget_text_embedding(clamped)

    @staticmethod
    async def _rank(
        db_name: str,
        namespace: str,
        summaries: dict[str, KnowledgeDocumentSummary],
        embedding: list[float],
        documents: int,
        passages_per_document: int,
    ) -> list[KnowledgeSemanticMatch]:
        """The best `documents` of one namespace, one filtered search per batch of ids."""
        store = await asyncio.to_thread(
            MilvusVectorStoreConfig(collection_name=db_name, index_namespaces=[namespace]).to_llama_index
        )
        hits: list[DocumentPassageHit] = []
        for batch in batched(summaries, IDS_PER_FILTER):
            expression = f"{NAMESPACE} == {json.dumps(namespace)} and {DOCUMENT_ID} in {json.dumps(list(batch))}"
            hits.extend(
                await asyncio.to_thread(
                    store.passages_grouped_by_document,
                    embedding,
                    [namespace],
                    expression,
                    documents,
                    passages_per_document,
                )
            )
        return KnowledgeSemanticSearch._matches(hits, summaries)

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
