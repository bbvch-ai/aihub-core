import re

from swiss_ai_hub.core.generative_ai import (
    KnowledgeContentMatch,
    KnowledgeContentSearchResult,
    KnowledgeContentSearchTimeoutError,
    KnowledgeDocument,
    KnowledgeDocumentSummary,
    KnowledgeSemanticMatch,
    KnowledgeSemanticRanking,
)

from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_run_scope import (
    KnowledgeDocumentRunScope,
)

_PASSAGES_SHOWN = 2
_PASSAGE_CHARS = 200
_NOISE = re.compile(r"(?:\s|\||-{3,}|█)+")
# Repeated in the result because models given a row condition kept reading documents to check it although the system
# prompt said not to; the latest tool result is what they act on.
_RANKING_NEXT = (
    "Next: keep the documents that are the kind of document the user asks about and leave out the others; do not read "
    "them to check a condition on their rows (an amount, a cap, a date), since the extraction checks it in every "
    "selected document."
)


class KnowledgeDocumentToolOutput:
    """How the document tools word their results for the model: compact lines, with the position and what to do next
    first, so a result cut to the loop's room never loses where to continue.

    In English whatever the run's locale, like the tool descriptions: the model reads these, never the user.
    """

    @staticmethod
    def listing(
        scope: KnowledgeDocumentRunScope, documents: list[KnowledgeDocumentSummary], offset: int, total: int
    ) -> str:
        end = offset + len(documents)
        position = f"Documents {offset + 1}-{end} of {total}" if documents else f"No documents at offset {offset}"
        more = f"; more with offset={end}" if end < total else ""
        lines = [KnowledgeDocumentToolOutput._entry(scope, document) for document in documents]
        return "\n".join([f"{position}{more}. {scope.describe()}", "id | collection | path | pages", *lines])

    @staticmethod
    def nothing_listed(scope: KnowledgeDocumentRunScope, examples: list[KnowledgeDocumentSummary]) -> str:
        shapes = ", ".join(f"'{document.path}'" for document in examples) or "none, the collections are empty"
        return (
            f"No document path matches. {scope.describe()} Paths look like: {shapes}. "
            "Try a broader glob such as '**/*name*', other file extensions, or a regex."
        )

    @staticmethod
    def search(scope: KnowledgeDocumentRunScope, result: KnowledgeContentSearchResult, offset: int) -> str:
        if not result.matches:
            return (
                f"No document contains this. {scope.describe()} "
                "Try fewer or other words, another spelling, or is_regex with alternatives such as 'Acme|ACME AG'."
            )
        end = offset + len(result.matches)
        more = f"; more with offset={result.next_offset}" if result.next_offset is not None else ""
        header = f"Documents {offset + 1}-{end} of {result.total_documents} that contain it{more}. {scope.describe()}"
        return "\n".join([header, *(KnowledgeDocumentToolOutput._match(scope, match) for match in result.matches)])

    @staticmethod
    def ranking(
        scope: KnowledgeDocumentRunScope, ranking: KnowledgeSemanticRanking, offset: int, page_size: int
    ) -> str:
        """One page of a ranking; its coverage comes before the page, so a model never takes it for the whole scope."""
        page = ranking.matches[offset : offset + page_size]
        coverage = KnowledgeDocumentToolOutput._coverage(ranking)
        if not page:
            return (
                f"No ranked documents at offset {offset}: the ranking holds {len(ranking.matches)}. {coverage} "
                f"{scope.describe()}"
            )
        end = offset + len(page)
        more = f"; more with offset={end}" if end < len(ranking.matches) else "; the ranking ends here"
        header = (
            f"Documents {offset + 1}-{end} of {len(ranking.matches)} ranked, most similar first{more}. {coverage} "
            f"{scope.describe()}"
        )
        lines = [header, "id | collection | path | pages | similarity"]
        lines.extend(KnowledgeDocumentToolOutput._ranked(scope, match) for match in page)
        lines.append(_RANKING_NEXT)
        return "\n".join(lines)

    @staticmethod
    def ranking_unavailable(problem: Exception) -> str:
        cause = (
            f"Ranking by meaning did not finish within {problem.timeout_seconds:g} s."
            if isinstance(problem, KnowledgeContentSearchTimeoutError)
            else f"Ranking by meaning is unavailable right now ({problem})."
        )
        return f"{cause} Find the documents with list_knowledge_documents and search_knowledge_content instead."

    @staticmethod
    def _coverage(ranking: KnowledgeSemanticRanking) -> str:
        """What the ranking leaves out: documents past its cut, and documents with no passage to be ranked by."""
        ranked, in_scope = len(ranking.matches), ranking.documents_in_scope
        if not in_scope:
            return "No documents are in scope."
        if ranking.capped:
            reach = f"Ranked the {ranked} closest of the {in_scope} documents in scope; narrow with path_glob."
        else:
            reach = f"Ranked {ranked} of the {in_scope} documents in scope."
        if not ranking.unranked:
            return reach
        return (
            f"{reach} {ranking.unranked} have no indexed passages and are not ranked at all; "
            "list_knowledge_documents and search_knowledge_content still find them."
        )

    @staticmethod
    def _ranked(scope: KnowledgeDocumentRunScope, match: KnowledgeSemanticMatch) -> str:
        passages = "\n".join(
            f"  > {KnowledgeDocumentToolOutput._compact(passage.text)}" for passage in match.passages[:_PASSAGES_SHOWN]
        )
        return f"{KnowledgeDocumentToolOutput._entry(scope, match.summary)} | {match.score:.2f}\n{passages}"

    @staticmethod
    def _compact(text: str) -> str:
        """A passage on one line: table rules and runs of whitespace say nothing about what a document is."""
        flat = _NOISE.sub(" ", text).strip()
        return flat if len(flat) <= _PASSAGE_CHARS else f"{flat[:_PASSAGE_CHARS]}…"

    @staticmethod
    def excerpt(scope: KnowledgeDocumentRunScope, document: KnowledgeDocument) -> str:
        summary = document.summary
        rest = (
            f" More with start={document.end}."
            if document.end < document.text_length
            else " This is the end of the document."
        )
        header = (
            f"{summary.path} in {scope.identifier_of(summary.collection)} (id {summary.id}): "
            f"characters {document.start}-{document.end} of {document.text_length}.{rest}"
        )
        return f"{header}\n\n{document.text}"

    @staticmethod
    def _entry(scope: KnowledgeDocumentRunScope, document: KnowledgeDocumentSummary) -> str:
        pages = document.number_of_pages if document.number_of_pages is not None else "-"
        return f"{document.id} | {scope.identifier_of(document.collection)} | {document.path} | {pages}"

    @staticmethod
    def _match(scope: KnowledgeDocumentRunScope, match: KnowledgeContentMatch) -> str:
        lines = "\n".join(f"  line {line.line_number} at {line.start}: {line.text}" for line in match.lines)
        count = f" ({match.matching_line_count} matching lines)" if match.matching_line_count > len(match.lines) else ""
        return f"{KnowledgeDocumentToolOutput._entry(scope, match.summary)}{count}\n{lines}"
