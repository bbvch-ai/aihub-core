import asyncio
from typing import Annotated

from opentelemetry import trace
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
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_text_index import KnowledgeTextIndex
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_text_index_query import KnowledgeTextIndexQuery
from swiss_ai_hub.core.generative_ai.knowledge_documents.path_glob import PathGlob
from swiss_ai_hub.core.generative_ai.knowledge_documents.resolved_knowledge_collection import (
    ResolvedKnowledgeCollection,
)
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.rag.documents.entities.ref_doc import RefDoc

# DocumentDB's error code for a regular expression its PCRE2 engine cannot compile.
_PCRE_REJECTED = 51091
# DocumentDB rejects every numbered backreference, `\1` and `\g{-1}` alike, with this message; named ones work.
_NUMBERED_REFERENCE = "reference to non-existent subpattern"

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
        index_query = KnowledgeTextIndexQuery.from_query(query, is_regex, case_sensitive)
        glob = None if path_glob is None else PathGlob(path_glob)
        resolved = await KnowledgeCollectionResolver.resolve_all(collections)
        try:
            candidates = await KnowledgeContentSearch._candidates(resolved, pattern, index_query, glob, budget)
            matches, next_index, dropped = await KnowledgeContentSearch._page(
                candidates, offset, pattern, limits, budget
            )
        except ExecutionTimeout as execution_timeout:
            raise budget.exhausted() from execution_timeout
        except OperationFailure as operation_failure:
            if operation_failure.code != _PCRE_REJECTED:
                raise
            raise KnowledgeContentSearch._rejected(query, operation_failure) from operation_failure
        return KnowledgeContentSearchResult(
            matches=matches,
            total_documents=len(candidates) - dropped,
            next_offset=next_index if next_index < len(candidates) else None,
        )

    @staticmethod
    def _rejected(query: str, operation_failure: OperationFailure) -> InvalidSearchPatternError:
        reason = (operation_failure.details or {}).get("errmsg", "")
        hint = (
            "numbered backreferences such as \\1 are not supported; name the group instead, as in (?P<x>ab)(?P=x)"
            if _NUMBERED_REFERENCE in reason
            else "use syntax PCRE2 and Python share"
        )
        return InvalidSearchPatternError(query, f"the database's regex engine (PCRE2) rejects it: {reason}; {hint}")

    @staticmethod
    async def _candidates(
        resolved: list[ResolvedKnowledgeCollection],
        pattern: KnowledgeContentPattern,
        index_query: KnowledgeTextIndexQuery | None,
        glob: PathGlob | None,
        budget: KnowledgeSearchBudget,
    ) -> list[_Candidate]:
        """Ids of the documents the database matched, collection by collection; the source is loaded only for a glob,
        since every extra field read costs a decompression of the whole row."""
        index_ids = await KnowledgeContentSearch._index_candidates(resolved, index_query, budget)
        per_collection = await asyncio.gather(
            *(
                KnowledgeContentSearch._matching_ids(
                    collection, pattern, index_ids.get(collection.db_name), glob is not None, budget
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
    async def _index_candidates(
        resolved: list[ResolvedKnowledgeCollection],
        index_query: KnowledgeTextIndexQuery | None,
        budget: KnowledgeSearchBudget,
    ) -> dict[str, list[str] | None]:
        """Candidates per knowledge database from the trigram index, given at most half the budget and never more than
        `MAX_INDEX_SECONDS`, so the scan still has the rest whenever the index cannot answer."""
        db_names = list(dict.fromkeys(collection.db_name for collection in resolved))
        index_ids: dict[str, list[str] | None] = (
            {}
            if index_query is None
            else await KnowledgeTextIndex.candidate_ids(db_names, index_query, budget.remaining_seconds() / 2)
        )
        served = [ids for ids in index_ids.values() if ids is not None]
        span = trace.get_current_span()
        span.set_attribute("knowledge.content_search.index_databases", len(served))
        span.set_attribute("knowledge.content_search.scan_databases", len(db_names) - len(served))
        span.set_attribute("knowledge.content_search.index_candidates", sum(len(ids) for ids in served))
        return index_ids

    @staticmethod
    async def _matching_ids(
        collection: ResolvedKnowledgeCollection,
        pattern: KnowledgeContentPattern,
        candidate_ids: list[str] | None,
        with_source: bool,
        budget: KnowledgeSearchBudget,
    ) -> list[RefDoc]:
        """FerretDB decides the final set either way, with the scan's own filter; the index only narrows the rows it
        reads, and no candidate means no match."""
        namespace = collection.collection.namespace_name
        if candidate_ids is None:
            return await asyncio.to_thread(
                RefDoc.search_ingested_ids,
                collection.db_name,
                namespace,
                pattern.database_pattern,
                pattern.database_options,
                budget.remaining_ms(),
                with_source,
            )
        if not candidate_ids:
            return []
        return await asyncio.to_thread(
            RefDoc.search_ingested_ids_among,
            collection.db_name,
            namespace,
            pattern.database_pattern,
            pattern.database_options,
            candidate_ids,
            budget.remaining_ms(),
            with_source,
        )

    @staticmethod
    async def _page(
        candidates: list[_Candidate],
        offset: int,
        pattern: KnowledgeContentPattern,
        limits: KnowledgeContentSearchLimits,
        budget: KnowledgeSearchBudget,
    ) -> tuple[list[KnowledgeContentMatch], int, int]:
        """Read candidates from `offset` until the page is full, dropping those without a line Python matches.

        Candidates are loaded one at a time, so at most one document's text is held while its lines are found,
        however large the documents on the page. Returns the page, the index after its last candidate, and how many
        candidates were dropped.
        """
        matches: list[KnowledgeContentMatch] = []
        index, dropped = offset, 0
        while index < len(candidates) and len(matches) < limits.max_documents:
            collection, document_id = candidates[index]
            index += 1
            ref_doc = await asyncio.to_thread(
                RefDoc.first_ingested_with_text,
                collection.db_name,
                collection.collection.namespace_name,
                document_id,
                budget.remaining_ms(),
            )
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
