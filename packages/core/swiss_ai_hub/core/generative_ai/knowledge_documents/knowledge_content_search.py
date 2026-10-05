import asyncio
from itertools import groupby
from typing import Annotated

from pymongo.errors import ExecutionTimeout, OperationFailure

from swiss_ai_hub.core.generative_ai.knowledge_documents.invalid_search_pattern_error import InvalidSearchPatternError
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_collection_resolver import (
    KnowledgeCollectionResolver,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_match import KnowledgeContentMatch
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_pattern import KnowledgeContentPattern
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_search_limits import (
    KnowledgeContentSearchLimits,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_search_result import (
    KnowledgeContentSearchResult,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_search_budget import KnowledgeSearchBudget
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_glob import PathGlob
from swiss_ai_hub.core.generative_ai.knowledge_documents.resolved_knowledge_collection import (
    ResolvedKnowledgeCollection,
)
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.rag.documents.entities.ref_doc import RefDoc

# DocumentDB's error code for a regular expression its PCRE2 engine cannot compile.
_PCRE_REJECTED = 51091

type _Candidate = tuple[ResolvedKnowledgeCollection, str]


class KnowledgeContentSearch:
    """Exact-term and regex search over the parsed text of knowledge documents, independent of any agent.

    Unlike vector or BM25 retrieval, which rank chunks and return the top few, this returns every fully ingested
    document whose text matches, page by page, with the matching lines located by character offset. It reads the
    document store that ingestion writes, so a document is found as soon as it is ingested and no longer found once it
    changes or is deleted, and nothing is indexed for it.

    Callers pass the collections the run may read, and the search trusts that list exactly as `KnowledgeDocumentReader`
    does: it must be the agent's configured collections narrowed to those the asking user may read, never a model's
    tool arguments. The query, the regex flag, the glob and the offset are safe to take from a model.
    """

    @staticmethod
    @trace_fn
    async def search(
        collections: Annotated[list[BucketNamespacePair], "Collections the caller may read; nothing else is searched"],
        query: Annotated[str, "Term to find, or a regular expression when `is_regex` is set"],
        *,
        is_regex: Annotated[bool, "Whether `query` is a regular expression rather than literal text"] = False,
        case_sensitive: Annotated[bool, "Whether letter case must match; by default it is ignored"] = False,
        path_glob: Annotated[str | None, "Only documents whose path matches this glob, as in `matching_glob`"] = None,
        offset: Annotated[int, "Position of the first document to return, from a previous `next_offset`"] = 0,
        limits: Annotated[KnowledgeContentSearchLimits | None, "Page size, line caps and time budget"] = None,
    ) -> KnowledgeContentSearchResult:
        """Documents whose parsed text matches, ordered by collection and document id so pages never overlap."""
        limits = limits or KnowledgeContentSearchLimits()
        budget = KnowledgeSearchBudget(limits.timeout_seconds)
        if offset < 0:
            raise ValueError(f"offset must not be negative, got {offset}")
        pattern = KnowledgeContentPattern(query, is_regex=is_regex, case_sensitive=case_sensitive)
        glob = None if path_glob is None else PathGlob(path_glob)
        resolved = await KnowledgeCollectionResolver.resolve_all(collections)
        try:
            candidates = await KnowledgeContentSearch._candidates(resolved, pattern, glob, budget)
            matches, next_index, dropped = await KnowledgeContentSearch._page(
                candidates, offset, pattern, limits, budget
            )
        except ExecutionTimeout as execution_timeout:
            raise budget.exhausted() from execution_timeout
        except OperationFailure as operation_failure:
            if operation_failure.code != _PCRE_REJECTED:
                raise
            reason = (operation_failure.details or {}).get("errmsg", "")
            raise InvalidSearchPatternError(
                query, f"the database's regex engine (PCRE2) rejects it: {reason}; use syntax PCRE2 and Python share"
            ) from operation_failure
        return KnowledgeContentSearchResult(
            matches=matches,
            total_documents=len(candidates) - dropped,
            next_offset=next_index if next_index < len(candidates) else None,
        )

    @staticmethod
    async def _candidates(
        resolved: list[ResolvedKnowledgeCollection],
        pattern: KnowledgeContentPattern,
        glob: PathGlob | None,
        budget: KnowledgeSearchBudget,
    ) -> list[_Candidate]:
        """Ids of the documents the database matched, collection by collection; the source is loaded only for a glob,
        since every extra field read costs a decompression of the whole row."""
        per_collection = await asyncio.gather(
            *(
                asyncio.to_thread(
                    RefDoc.search_ingested_ids,
                    collection.db_name,
                    collection.collection.namespace_name,
                    pattern.database_pattern,
                    pattern.database_options,
                    budget.remaining_ms(),
                    glob is not None,
                )
                for collection in resolved
            )
        )
        ordered = sorted(
            zip(resolved, per_collection, strict=True),
            key=lambda pair: (pair[0].collection.bucket_name, pair[0].collection.namespace_name),
        )
        return [
            (collection, str(ref_doc.id))
            for collection, ref_docs in ordered
            for ref_doc in ref_docs
            if glob is None or glob.matches(collection.relative_path(ref_doc.data.metadata.source))
        ]

    @staticmethod
    async def _page(
        candidates: list[_Candidate],
        offset: int,
        pattern: KnowledgeContentPattern,
        limits: KnowledgeContentSearchLimits,
        budget: KnowledgeSearchBudget,
    ) -> tuple[list[KnowledgeContentMatch], int, int]:
        """Read candidates from `offset` until the page is full, dropping those without a line Python matches.

        Returns the page, the index after its last candidate, and how many candidates were dropped.
        """
        matches: list[KnowledgeContentMatch] = []
        index, dropped = offset, 0
        while index < len(candidates) and len(matches) < limits.max_documents:
            batch = candidates[index : index + limits.max_documents - len(matches)]
            index += len(batch)
            loaded = await KnowledgeContentSearch._load(batch, budget)
            for collection, document_id in batch:
                ref_doc = loaded.get((collection.db_name, document_id))
                match = (
                    None
                    if ref_doc is None
                    else await KnowledgeContentSearch._match(ref_doc, collection, pattern, limits, budget)
                )
                if match is None:
                    dropped += 1
                else:
                    matches.append(match)
        return matches, index, dropped

    @staticmethod
    async def _load(batch: list[_Candidate], budget: KnowledgeSearchBudget) -> dict[tuple[str, str], RefDoc]:
        """Text and metadata of a batch, one query per collection; candidates are grouped by collection already."""
        groups = [
            (collection, [document_id for _, document_id in members])
            for collection, members in groupby(batch, key=lambda candidate: candidate[0])
        ]
        per_collection = await asyncio.gather(
            *(
                asyncio.to_thread(
                    RefDoc.ingested_with_text_by_ids,
                    collection.db_name,
                    collection.collection.namespace_name,
                    ids,
                    budget.remaining_ms(),
                )
                for collection, ids in groups
            )
        )
        return {
            (collection.db_name, str(ref_doc.id)): ref_doc
            for (collection, _), ref_docs in zip(groups, per_collection, strict=True)
            for ref_doc in ref_docs
        }

    @staticmethod
    async def _match(
        ref_doc: RefDoc,
        collection: ResolvedKnowledgeCollection,
        pattern: KnowledgeContentPattern,
        limits: KnowledgeContentSearchLimits,
        budget: KnowledgeSearchBudget,
    ) -> KnowledgeContentMatch | None:
        lines, matching_line_count = await asyncio.to_thread(
            pattern.matching_lines, ref_doc.data.text or "", limits, budget
        )
        if matching_line_count == 0:
            return None
        return KnowledgeContentMatch(
            summary=KnowledgeDocumentSummary.from_ref_doc(ref_doc, collection),
            lines=lines,
            matching_line_count=matching_line_count,
        )
