import logging
from typing import Annotated

from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.generative_ai import (
    BucketNamespacePair,
    InvalidSearchPatternError,
    KnowledgeContentSearch,
    KnowledgeContentSearchTimeoutError,
    KnowledgeDocumentSummary,
    KnowledgeSearchBudget,
    KnowledgeSemanticSearch,
    KnowledgeSemanticSearchUnavailableError,
)

from swiss_ai_hub.agent.capabilities.record_extraction.selection_facets import SelectionFacets

logger = logging.getLogger(__name__)

# Above this many documents one answer would run for long, so the user first sees a sample, what it will cost and the
# columns, and confirms. Fixed rather than a setting: it is about the user's patience, not the profile.
SAMPLE_ABOVE_DOCUMENTS = 100
# Documents a selection too large to extract unasked shows rows from before the user confirms; a few more than the
# three a narrowed selection needed, because over a whole scope a document picked at random often holds no wanted row.
SAMPLE_DOCUMENTS = 5
# One budget for both term scans; ordering is a convenience, so a slow scan leaves the order as it was.
EVIDENCE_TIMEOUT_SECONDS = 15.0

type _Key = tuple[str, str, str]


class ExtractionSample:
    """Puts the documents likely to hold wanted rows first, without leaving any out.

    The sample of a large selection shows the user what the whole table will hold, so it must come from documents
    with wanted rows: a folder spread over a whole scope, with a condition such as "Hooli hardware", mostly shows
    other suppliers' invoices and no row at all. When the profile ranks by meaning, the ranking of the request decides
    the order; otherwise, or when ranking is unavailable, the evidence is lexical, one id-only scan per term:
    documents whose text contains the terms that identify them (a supplier) come first, then those with the row
    terms, then the rest in their order. The same order lets the documents most likely to matter be read first.
    """

    @staticmethod
    async def ordered(
        documents: Annotated[list[KnowledgeDocumentSummary], "The selected documents, in order"],
        collections: Annotated[list[BucketNamespacePair], "Collections the run may read"],
        document_terms: Annotated[str | None, "Words or a pattern documents holding wanted rows contain"],
        row_terms: Annotated[str | None, "Words or a pattern the wanted lines contain"],
        *,
        semantic_query: Annotated[
            str | None, "What the wanted documents are about; ranks by meaning when given"
        ] = None,
        user: Annotated[UserIdentity | None, "Whose key embeds the query"] = None,
        path_glob: Annotated[str | None, "The profile's glob, so the ranking spends its places on the scope"] = None,
    ) -> tuple[list[KnowledgeDocumentSummary], int]:
        """The documents, those with evidence first, and how many lead with evidence. A ranking that failed, ran out
        of time or placed none of the documents leaves the term scans a budget of their own."""
        if semantic_query and semantic_query.strip():
            ranking_budget = KnowledgeSearchBudget(EVIDENCE_TIMEOUT_SECONDS)
            ranked = await ExtractionSample._ranked(
                documents, collections, semantic_query, user, ranking_budget, path_glob
            )
            if ranked is not None and ranked[1]:
                return ranked
        budget = KnowledgeSearchBudget(EVIDENCE_TIMEOUT_SECONDS)
        identifying = await ExtractionSample._matching(collections, document_terms, budget)
        with_rows = await ExtractionSample._matching(collections, row_terms, budget)
        if not identifying and not with_rows:
            return documents, 0

        def evidence(document: KnowledgeDocumentSummary) -> int:
            key = ExtractionSample._key(document)
            return 2 * (key in identifying) + (key in with_rows)

        ordered = sorted(documents, key=lambda document: -evidence(document))
        return ordered, sum(1 for document in ordered if evidence(document))

    @staticmethod
    def pick(
        ordered: Annotated[list[KnowledgeDocumentSummary], "Documents, the likeliest first"],
        size: Annotated[int, "How many documents the sample holds"] = SAMPLE_DOCUMENTS,
        likely: Annotated[int, "How many leading documents carry evidence"] = 0,
    ) -> list[KnowledgeDocumentSummary]:
        """The likeliest documents, filled up with a spread over the largest folders when too few carry evidence."""
        chosen = ordered[: min(size, likely)]
        if len(chosen) < size:
            rest = [document for document in ordered if document not in chosen]
            chosen.extend(SelectionFacets.sample(rest, size - len(chosen)))
        return chosen

    @staticmethod
    async def _ranked(
        documents: list[KnowledgeDocumentSummary],
        collections: list[BucketNamespacePair],
        query: str,
        user: UserIdentity | None,
        budget: KnowledgeSearchBudget,
        path_glob: str | None,
    ) -> tuple[list[KnowledgeDocumentSummary], int] | None:
        """The documents in the ranking's order, those without a passage after; None when ranking is unavailable."""
        try:
            ranking = await KnowledgeSemanticSearch.rank(
                collections,
                query,
                path_globs=[path_glob] if path_glob else None,
                passages_per_document=1,
                user=user,
                budget=budget,
            )
        except (KnowledgeSemanticSearchUnavailableError, KnowledgeContentSearchTimeoutError) as problem:
            logger.info("[record-extraction] no ranking, ordering by terms: %s", problem)
            return None
        position = {ExtractionSample._key(match.summary): index for index, match in enumerate(ranking.matches)}
        ordered = sorted(documents, key=lambda document: position.get(ExtractionSample._key(document), len(position)))
        return ordered, sum(1 for document in documents if ExtractionSample._key(document) in position)

    @staticmethod
    async def _matching(
        collections: list[BucketNamespacePair], terms: str | None, budget: KnowledgeSearchBudget
    ) -> set[_Key]:
        """The documents whose text matches the terms, read as a pattern and, when that is invalid, as text."""
        if not terms or not terms.strip():
            return set()
        try:
            try:
                return await KnowledgeContentSearch.matching_ids(collections, terms, budget, is_regex=True)
            except InvalidSearchPatternError:
                return await KnowledgeContentSearch.matching_ids(collections, terms, budget)
        except (KnowledgeContentSearchTimeoutError, InvalidSearchPatternError) as problem:
            logger.info("[record-extraction] no evidence from %r: %s", terms, problem)
            return set()

    @staticmethod
    def _key(document: KnowledgeDocumentSummary) -> _Key:
        return document.collection.bucket_name, document.collection.namespace_name, document.id
