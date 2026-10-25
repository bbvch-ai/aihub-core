from typing import Annotated, Any

from llama_index.core.tools.tool_spec.base import BaseToolSpec
from swiss_ai_hub.core.generative_ai import (
    KnowledgeContentSearch,
    KnowledgeContentSearchLimits,
    KnowledgeDocument,
    KnowledgeDocumentListing,
    KnowledgeDocumentNotFoundError,
    KnowledgeDocumentPendingError,
    KnowledgeDocumentReader,
    KnowledgeSemanticSearch,
)

from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_fields import KnowledgeDocumentFields
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_run_scope import (
    KnowledgeDocumentRunScope,
)
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_scope import KnowledgeDocumentScope
from swiss_ai_hub.agent.capabilities.knowledge_documents.knowledge_document_tool_output import (
    KnowledgeDocumentToolOutput,
)
from swiss_ai_hub.agent.capabilities.tool_loop.tool_context import ToolContext
from swiss_ai_hub.agent.capabilities.tool_loop.tool_options import ToolOptions
from swiss_ai_hub.agent.i18n.agent_locale_string import AgentLocaleString

LIST_KNOWLEDGE_DOCUMENTS_TOOL = "list_knowledge_documents"
SEARCH_KNOWLEDGE_CONTENT_TOOL = "search_knowledge_content"
READ_KNOWLEDGE_DOCUMENT_TOOL = "read_knowledge_document"
RANK_KNOWLEDGE_DOCUMENTS_TOOL = "rank_knowledge_documents"

# Sized so a page stays well inside the loop's default result room (4,000 tokens): a cut page loses its last entries.
LISTING_PAGE_SIZE = 60
SEARCH_PAGE_LIMITS = KnowledgeContentSearchLimits(max_documents=20, max_lines_per_document=2, max_line_chars=160)
RANKING_PAGE_SIZE = 15
# Five passages rank a document (one strong passage in a long document is not enough to tell what it is about); two
# of them are shown, which with the page size keeps a page near 2,500 tokens.
RANKING_PASSAGES = 5
READ_CHARACTERS = 12_000
_EXAMPLE_PATHS = 3


class KnowledgeDocumentTools(BaseToolSpec):
    """Whole knowledge documents for the model: list and match their paths, search their text, read them, and, when
    the profile enables it, rank them by meaning.

    Vector search returns similar excerpts; these return every match and whole files, which questions about exact
    terms, all documents of a kind, or one document's full content need. The ranking is vector search grouped by
    document and confined to the same documents, for the documents a request describes in other words. Offered only when the profile switches them
    on, and only over the collections the asking user may read, cut to the profile's glob before the model sees any.
    Errors raise, so the loop marks them as failed calls and the model can retry with what the message says.
    """

    spec_functions = [
        LIST_KNOWLEDGE_DOCUMENTS_TOOL,
        SEARCH_KNOWLEDGE_CONTENT_TOOL,
        READ_KNOWLEDGE_DOCUMENT_TOOL,
        RANK_KNOWLEDGE_DOCUMENTS_TOOL,
    ]

    def __init__(self, context: ToolContext) -> None:
        self.context = context
        config = context.agent_config
        if not isinstance(config, KnowledgeDocumentFields) or not config.knowledge_documents.enabled:
            self.spec_functions = []
        elif not config.knowledge_documents.semantic_search:
            self.spec_functions = [name for name in self.spec_functions if name != RANK_KNOWLEDGE_DOCUMENTS_TOOL]

    @staticmethod
    def _options(tool: str) -> dict[str, Any]:
        return {
            "label": AgentLocaleString.from_i18n_path(f"agent.knowledge_documents.tools.{tool}.label"),
            "approval_summary": AgentLocaleString.from_i18n_path(f"agent.knowledge_documents.tools.{tool}.approval"),
        }

    @ToolOptions.of(**_options(LIST_KNOWLEDGE_DOCUMENTS_TOOL))
    async def list_knowledge_documents(
        self,
        path_glob: Annotated[str, "Glob on the path in its collection, e.g. 'invoices/2025/**'; '**' lists all."],
        path_regex: Annotated[str | None, "A regular expression the path must also contain, e.g. '(?i)acme'."] = None,
        offset: Annotated[int, "Where the page starts, from a previous result's 'more with offset='."] = 0,
    ) -> str:
        """Lists the documents of our knowledge collections whose path matches, with ids for the other document
        tools. Use it to find documents by name, folder, year or file type, or to see what a collection holds. Paths
        are matched ignoring case; a glob that is too narrow misses files, so prefer '**/*acme*' over '*.pdf'."""
        scope = await KnowledgeDocumentScope.for_tool(self.context)
        everything = await KnowledgeDocumentReader.list_documents(scope.pairs())
        allowed = everything.matching_glob(scope.restricting_glob) if scope.restricting_glob else everything
        matching = allowed.matching_glob(path_glob)
        if path_regex:
            matching = matching.matching_regex(path_regex)
        if not matching.documents:
            return KnowledgeDocumentToolOutput.nothing_listed(scope, allowed.documents[:_EXAMPLE_PATHS])
        page = matching.documents[offset : offset + LISTING_PAGE_SIZE]
        return KnowledgeDocumentToolOutput.listing(scope, page, offset, matching.total)

    @ToolOptions.of(**_options(SEARCH_KNOWLEDGE_CONTENT_TOOL))
    async def search_knowledge_content(
        self,
        query: Annotated[str, "Exact text to find, e.g. a supplier, an order number or 'RFC 9000'."],
        is_regex: Annotated[bool, "Whether the query is a regular expression, e.g. 'Acme( AG)?|ACME'."] = False,
        case_sensitive: Annotated[bool, "Whether letter case must match; ignored by default."] = False,
        path_glob: Annotated[str | None, "Only documents whose path matches this glob."] = None,
        offset: Annotated[int, "Where the page starts, from a previous result's 'more with offset='."] = 0,
    ) -> str:
        """Finds every knowledge document whose text contains the query, with the matching lines and ids. Unlike
        the knowledge search, which returns similar excerpts, this finds exact terms in all documents, so use it for
        names, numbers and codes, or to find all documents that mention something."""
        scope = await KnowledgeDocumentScope.for_tool(self.context)
        globs = [glob for glob in (scope.restricting_glob, path_glob) if glob]
        result = await KnowledgeContentSearch.search(
            scope.pairs(),
            query,
            is_regex=is_regex,
            case_sensitive=case_sensitive,
            path_globs=globs,
            offset=offset,
            limits=SEARCH_PAGE_LIMITS,
        )
        return KnowledgeDocumentToolOutput.search(scope, result, offset)

    @ToolOptions.of(**_options(RANK_KNOWLEDGE_DOCUMENTS_TOOL))
    async def rank_knowledge_documents(
        self,
        query: Annotated[
            str,
            "What the wanted documents are about, in a few words, e.g. 'supplier contract liability termination'; "
            "no amounts, dates or thresholds.",
        ],
        path_glob: Annotated[str | None, "Only documents whose path matches this glob."] = None,
        offset: Annotated[int, "Where the page starts, from a previous result's 'more with offset='."] = 0,
    ) -> str:
        """Ranks every knowledge document by how closely its passages match the meaning of the query, most similar
        first, with ids and its closest passages. It finds documents written in other words or another language than
        the query, such as a German 'Haftungsbeschränkung' for 'liability cap'. A ranking is not a filter: every
        document has a place in it, so judge each one by its path and passages, and read the next page while the last
        documents are still relevant."""
        scope = await KnowledgeDocumentScope.for_tool(self.context)
        globs = [glob for glob in (scope.restricting_glob, path_glob) if glob]
        result = await KnowledgeSemanticSearch.search(
            scope.pairs(),
            query,
            path_globs=globs,
            offset=max(offset, 0),
            limit=RANKING_PAGE_SIZE,
            passages_per_document=RANKING_PASSAGES,
            user=self.context.user,
        )
        return KnowledgeDocumentToolOutput.ranking(scope, result, max(offset, 0))

    @ToolOptions.of(**_options(READ_KNOWLEDGE_DOCUMENT_TOOL))
    async def read_knowledge_document(
        self,
        document_id: Annotated[str, "The document's id, from a listing or a search."],
        start: Annotated[
            int, "The first character to read: a search line's 'at' position, or the 'more with start=' value."
        ] = 0,
    ) -> str:
        """Reads a knowledge document's text, a part at a time: each call returns about 3,000 tokens and says where
        to continue. Use it to answer from one document's full content; to find documents use the other tools. For a
        long document, start at the 'at' position a search gives a matching line instead of reading from the
        beginning."""
        scope = await KnowledgeDocumentScope.for_tool(self.context)
        document = await self._load(scope, document_id, max(start, 0))
        if (
            scope.restricting_glob
            and not KnowledgeDocumentListing.from_summaries([document.summary])
            .matching_glob(scope.restricting_glob)
            .documents
        ):
            raise LookupError(self._no_access(scope, document_id))
        return KnowledgeDocumentToolOutput.excerpt(scope, document)

    @staticmethod
    async def _load(scope: KnowledgeDocumentRunScope, document_id: str, start: int) -> KnowledgeDocument:
        try:
            return await KnowledgeDocumentReader.load_document(
                scope.pairs(), document_id, start, start + READ_CHARACTERS
            )
        except KnowledgeDocumentPendingError as pending:
            raise LookupError(
                f"Document {document_id} is still being ingested and cannot be read yet; try again later."
            ) from pending
        except KnowledgeDocumentNotFoundError as not_found:
            raise LookupError(KnowledgeDocumentTools._no_access(scope, document_id)) from not_found

    @staticmethod
    def _no_access(scope: KnowledgeDocumentRunScope, document_id: str) -> str:
        return (
            f"No access to a document with id {document_id}: it is not among the documents you may read here. "
            f"{scope.describe()} Do not use a document of the same name from elsewhere instead."
        )
