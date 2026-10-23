from typing import Annotated

from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_content_search import KnowledgeContentSearch
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_criteria import KnowledgeDocumentCriteria
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_listing import KnowledgeDocumentListing
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_reader import KnowledgeDocumentReader
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_selection import (
    KnowledgeDocumentSelection,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_selection_result import (
    KnowledgeDocumentSelectionResult,
)
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_document_summary import KnowledgeDocumentSummary
from swiss_ai_hub.core.generative_ai.knowledge_documents.knowledge_search_budget import KnowledgeSearchBudget
from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn

type _DocumentKey = tuple[str, str, str]


class KnowledgeDocumentSelector:
    """Resolves a `KnowledgeDocumentSelection` to the documents it describes, within the caller's collections and glob.

    The same trust rule as `KnowledgeDocumentReader` applies: `collections` and `restricting_glob` come from the caller
    and are never a model's arguments, while the selection may be. The restricting glob is applied before any criterion,
    so a selection can only narrow what the caller allows, whatever its own globs or ids say.

    One deadline covers the listing and every content query, and a content query is one id-only scan per collection, so
    resolving a broad selection costs the same as a narrow one: the caller learns how many documents match before
    anything is loaded or extracted.
    """

    @staticmethod
    @trace_fn
    async def resolve(
        collections: Annotated[list[BucketNamespacePair], "Collections the caller may read; nothing else is selected"],
        selection: Annotated[KnowledgeDocumentSelection, "The documents to pick, as a model described them"],
        limit: Annotated[int, "The most documents to return; more matches set `truncated`"],
        restricting_glob: Annotated[str | None, "Glob every selected path must match, set by the caller"] = None,
        timeout_seconds: Annotated[float, "Time budget for the listing and every content query together"] = 20.0,
    ) -> KnowledgeDocumentSelectionResult:
        budget = KnowledgeSearchBudget(timeout_seconds)
        listing = await KnowledgeDocumentReader.list_documents(collections, budget)
        if restricting_glob:
            listing = listing.matching_glob(restricting_glob)
        selected: dict[_DocumentKey, KnowledgeDocumentSummary] = {}
        for criteria in selection.any_of:
            documents = await KnowledgeDocumentSelector._matching(
                collections, listing, criteria, restricting_glob, budget
            )
            selected.update((KnowledgeDocumentSelector._key(document), document) for document in documents)
        ordered = KnowledgeDocumentListing.from_summaries(list(selected.values())).documents
        return KnowledgeDocumentSelectionResult(documents=ordered[:limit], truncated=len(ordered) > limit)

    @staticmethod
    async def _matching(
        collections: list[BucketNamespacePair],
        listing: KnowledgeDocumentListing,
        criteria: KnowledgeDocumentCriteria,
        restricting_glob: str | None,
        budget: KnowledgeSearchBudget,
    ) -> list[KnowledgeDocumentSummary]:
        if criteria.path_glob:
            listing = listing.matching_glob(criteria.path_glob)
        if criteria.path_regex:
            listing = listing.matching_regex(criteria.path_regex)
        if criteria.document_ids:
            wanted = set(criteria.document_ids)
            listing = listing.model_copy(update={"documents": [doc for doc in listing.documents if doc.id in wanted]})
        if criteria.content_query is None or not listing.documents:
            return listing.documents
        globs = [glob for glob in (restricting_glob, criteria.path_glob) if glob]
        matching = await KnowledgeContentSearch.matching_ids(
            collections, criteria.content_query, budget, is_regex=criteria.content_is_regex, path_globs=globs
        )
        return [document for document in listing.documents if KnowledgeDocumentSelector._key(document) in matching]

    @staticmethod
    def _key(document: KnowledgeDocumentSummary) -> _DocumentKey:
        return document.collection.bucket_name, document.collection.namespace_name, document.id
