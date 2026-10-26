from swiss_ai_hub.core.generative_ai import (
    KnowledgeContentMatch,
    KnowledgeContentSearchResult,
    KnowledgeDocument,
    KnowledgeDocumentSummary,
)

from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_run_scope import (
    KnowledgeDocumentRunScope,
)


class KnowledgeDocumentToolOutput:
    """How the document tools word their results for the model: compact lines, with the position and what to do next
    first, so a result cut to the loop's room never loses where to continue."""

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
